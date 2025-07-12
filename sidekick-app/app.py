"""
Sidekick Personal Co-Worker - Gradio Web Interface

This module provides a web-based interface for the Sidekick AI assistant using Gradio.
It handles user interactions, manages the Sidekick instance lifecycle, and provides
a clean chat interface for task execution.

Features:
- Real-time chat interface
- Success criteria input
- Conversation history management
- Instance lifecycle management
- Resource cleanup

Author: AI Course Project
License: MIT
"""

import gradio as gr
from sidekick import Sidekick


async def setup():
    """
    Initialize and set up a new Sidekick instance.
    
    This function creates a new Sidekick instance and performs the initial setup,
    including tool initialization and graph compilation.
    
    Returns:
        Sidekick: Configured and ready-to-use Sidekick instance
    """
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick

async def process_message(sidekick, message, success_criteria, history):
    """
    Process a user message through the Sidekick workflow.
    
    This function takes a user message and success criteria, processes them through
    the Sidekick workflow, and returns the updated conversation history.
    
    Args:
        sidekick: Active Sidekick instance
        message: User's input message
        success_criteria: Criteria for successful task completion
        history: Current conversation history
        
    Returns:
        tuple: (updated_history, sidekick_instance)
    """
    results = await sidekick.run_superstep(message, success_criteria, history)
    return results, sidekick
    
async def reset():
    """
    Reset the application to a clean state.
    
    This function creates a new Sidekick instance and clears all conversation
    history and input fields, effectively starting fresh.
    
    Returns:
        tuple: (empty_message, empty_criteria, empty_history, new_sidekick)
    """
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", None, new_sidekick

def free_resources(sidekick):
    """
    Clean up resources when the Sidekick instance is destroyed.
    
    This function is called automatically by Gradio when the Sidekick state
    is cleaned up, ensuring proper resource management and preventing memory leaks.
    
    Args:
        sidekick: Sidekick instance to clean up
    """
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


# Create the Gradio interface
with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick Personal Co-Worker")
    sidekick = gr.State(delete_callback=free_resources)
    
    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=300, type="messages")
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick")
        with gr.Row():
            success_criteria = gr.Textbox(show_label=False, placeholder="What are your success criteria?")
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")
        
    # Set up event handlers
    ui.load(setup, [], [sidekick])
    message.submit(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])
    success_criteria.submit(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])
    go_button.click(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])
    reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick])

# Launch the application
ui.launch(inbrowser=True)