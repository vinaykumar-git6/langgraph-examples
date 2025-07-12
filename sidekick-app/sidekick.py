"""
Sidekick Personal Co-Worker - Core Implementation

This module contains the main Sidekick class that implements an intelligent AI assistant
using LangGraph for workflow management. The assistant uses a worker-evaluator pattern
to continuously improve task completion until success criteria are met.

Key Features:
- Worker node that processes requests using LLM and tools
- Evaluator node that assesses task completion
- Router that determines workflow direction
- Memory management for conversation persistence
- Tool integration for web browsing, file operations, and more

Author: AI Course Project
License: MIT
"""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field
from sidekick_tools import playwright_tools, other_tools
import uuid
import asyncio
from datetime import datetime

# Load environment variables
load_dotenv(override=True)

class State(TypedDict):
    """
    State management for the Sidekick workflow.
    
    This TypedDict defines the structure of the state that flows through
    the LangGraph workflow, containing all necessary information for
    task processing and evaluation.
    
    Attributes:
        messages: List of conversation messages with automatic message merging
        success_criteria: User-defined criteria for task completion
        feedback_on_work: Previous feedback from evaluator (if any)
        success_criteria_met: Boolean flag indicating if criteria are satisfied
        user_input_needed: Boolean flag indicating if user input is required
    """
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


class EvaluatorOutput(BaseModel):
    """
    Structured output model for the evaluator node.
    
    This Pydantic model defines the structure of the evaluator's response,
    ensuring consistent and validated output for the workflow.
    
    Attributes:
        feedback: Detailed feedback on the assistant's response
        success_criteria_met: Whether the success criteria have been met
        user_input_needed: True if more input is needed from the user
    """
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(description="True if more input is needed from the user, or clarifications, or the assistant is stuck")


class Sidekick:
    """
    Main Sidekick class implementing an intelligent AI assistant.
    
    This class manages the entire workflow of the Sidekick assistant, including
    tool setup, LLM configuration, graph building, and task execution. It uses
    a worker-evaluator pattern to ensure high-quality task completion.
    
    Attributes:
        worker_llm_with_tools: LLM instance bound with tools for task execution
        evaluator_llm_with_output: LLM instance with structured output for evaluation
        tools: List of available tools for the assistant
        graph: Compiled LangGraph workflow
        sidekick_id: Unique identifier for this Sidekick instance
        memory: Memory saver for conversation persistence
        browser: Playwright browser instance for web automation
        playwright: Playwright instance for browser management
    """
    
    def __init__(self):
        """Initialize a new Sidekick instance with default values."""
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.llm_with_tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    async def setup(self):
        """
        Set up the Sidekick instance with tools, LLMs, and workflow graph.
        
        This method initializes all components needed for the Sidekick to function:
        - Playwright browser tools for web automation
        - Additional tools (search, file management, etc.)
        - Worker LLM with bound tools
        - Evaluator LLM with structured output
        - LangGraph workflow compilation
        
        Raises:
            Exception: If setup fails (e.g., API key issues, browser launch problems)
        """
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        await self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        """
        Worker node that processes user requests using LLM and tools.
        
        This method is the main processing node in the workflow. It:
        - Constructs a system message with current context and success criteria
        - Handles previous feedback if the task was previously attempted
        - Invokes the LLM with tools to process the request
        - Returns updated state with the LLM response
        
        Args:
            state: Current workflow state containing messages and criteria
            
        Returns:
            Dict containing updated messages with the LLM response
        """
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
    You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.
    You have many tools to help you, including tools to browse the internet, navigating and retrieving web pages.
    You have a tool to run python code, but note that you would need to include a print() statement if you wanted to receive output.
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    This is the success criteria:
    {state['success_criteria']}
    You should reply either with a question for the user about this assignment, or with your final response.
    If you have a question for the user, you need to reply by clearly stating your question. An example might be:

    Question: please clarify whether you want a summary or a detailed answer

    If you've finished, reply with the final answer, and don't ask a question; simply reply with the answer.
    """
        
        if state.get("feedback_on_work"):
            system_message += f"""
    Previously you thought you completed the assignment, but your reply was rejected because the success criteria was not met.
    Here is the feedback on why this was rejected:
    {state['feedback_on_work']}
    With this feedback, please continue the assignment, ensuring that you meet the success criteria or have a question for the user."""
        
        # Add in the system message

        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True
        
        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages
        
        # Invoke the LLM with tools
        response = self.worker_llm_with_tools.invoke(messages)
        
        # Return updated state
        return {
            "messages": [response],
        }


    def worker_router(self, state: State) -> str:
        """
        Router that determines the next step in the workflow.
        
        This method analyzes the last message from the worker to decide whether
        to route to the tools node (if tools were called) or to the evaluator
        node (if the worker provided a direct response).
        
        Args:
            state: Current workflow state containing messages
            
        Returns:
            String indicating the next node: "tools" or "evaluator"
        """
        last_message = state["messages"][-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
            return "evaluator"
        
    def format_conversation(self, messages: List[Any]) -> str:
        """
        Format conversation history for evaluation.
        
        This method converts the message history into a readable format
        for the evaluator to analyze the conversation flow.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Formatted string representation of the conversation
        """
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tools use]"
                conversation += f"Assistant: {text}\n"
        return conversation
        
    def evaluator(self, state: State) -> State:
        """
        Evaluator node that assesses task completion and provides feedback.
        
        This method evaluates the assistant's response against the success criteria
        and determines whether the task is complete, needs more work, or requires
        user input for clarification.
        
        Args:
            state: Current workflow state containing messages and criteria
            
        Returns:
            Updated state with evaluation results and feedback
        """
        last_response = state["messages"][-1].content

        system_message = f"""You are an evaluator that determines if a task has been completed successfully by an Assistant.
    Assess the Assistant's last response based on the given criteria. Respond with your feedback, and with your decision on whether the success criteria has been met,
    and whether more input is needed from the user."""
        
        user_message = f"""You are evaluating a conversation between the User and Assistant. You decide what action to take based on the last response from the Assistant.

    The entire conversation with the assistant, with the user's original request and all replies, is:
    {self.format_conversation(state['messages'])}

    The success criteria for this assignment is:
    {state['success_criteria']}

    And the final response from the Assistant that you are evaluating is:
    {last_response}

    Respond with your feedback, and decide if the success criteria is met by this response.
    Also, decide if more user input is required, either because the assistant has a question, needs clarification, or seems to be stuck and unable to answer without help.

    The Assistant has access to a tool to write files. If the Assistant says they have written a file, then you can assume they have done so.
    Overall you should give the Assistant the benefit of the doubt if they say they've done something. But you should reject if you feel that more work should go into this.

    """
        if state["feedback_on_work"]:
            user_message += f"Also, note that in a prior attempt from the Assistant, you provided this feedback: {state['feedback_on_work']}\n"
            user_message += "If you're seeing the Assistant repeating the same mistakes, then consider responding that user input is required."
        
        evaluator_messages = [SystemMessage(content=system_message), HumanMessage(content=user_message)]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)
        new_state = {
            "messages": [{"role": "assistant", "content": f"Evaluator Feedback on this answer: {eval_result.feedback}"}],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed
        }
        return new_state

    def route_based_on_evaluation(self, state: State) -> str:
        """
        Router that determines workflow continuation based on evaluation results.
        
        This method decides whether to end the workflow (if criteria are met or
        user input is needed) or continue with the worker node for more processing.
        
        Args:
            state: Current workflow state with evaluation results
            
        Returns:
            String indicating the next step: "END" or "worker"
        """
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        else:
            return "worker"


    async def build_graph(self):
        """
        Build and compile the LangGraph workflow.
        
        This method constructs the workflow graph with the following structure:
        START → worker → router → tools/evaluator → END
        
        The graph implements a worker-evaluator pattern where:
        - Worker processes requests using LLM and tools
        - Router determines whether to use tools or evaluate
        - Tools execute various operations (web browsing, file ops, etc.)
        - Evaluator assesses completion and provides feedback
        - Feedback loop continues until success or user input needed
        
        The graph is compiled with memory checkpointing for conversation persistence.
        """
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        # Add edges
        graph_builder.add_conditional_edges("worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"})
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges("evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END})
        graph_builder.add_edge(START, "worker")

        # Compile the graph
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        """
        Execute a complete workflow step with the given input.
        
        This method runs the entire workflow graph with the provided message
        and success criteria, returning the updated conversation history
        with the assistant's response and evaluator feedback.
        
        Args:
            message: User's input message
            success_criteria: Criteria for successful task completion
            history: Previous conversation history
            
        Returns:
            Updated conversation history with new messages and feedback
        """
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = {
            "messages": message,
            "success_criteria": success_criteria or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False
        }
        result = await self.graph.ainvoke(state, config=config)
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply, feedback]
    
    def cleanup(self):
        """
        Clean up resources used by the Sidekick instance.
        
        This method properly closes the browser and playwright instances
        to prevent resource leaks. It handles both async and sync contexts
        to ensure cleanup works in all scenarios.
        """
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                # If no loop is running, do a direct run
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())
