"""
Sidekick Tools Configuration

This module provides all the tools and toolkits used by the Sidekick assistant.
It includes web browsing capabilities, file management, search functionality,
and various utility tools for task execution.

Available Tools:
- Playwright browser tools for web automation
- File management toolkit for file operations
- Web search using Google Serper API
- Wikipedia search and query tools
- Python REPL for code execution
- Push notifications via Pushover

Author: AI Course Project
License: MIT
"""

from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import requests
from langchain.agents import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper



# Load environment variables
load_dotenv(override=True)

# Pushover notification configuration
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"

# Initialize search API wrapper
serper = GoogleSerperAPIWrapper()

async def playwright_tools():
    """
    Set up Playwright browser tools for web automation.
    
    This function initializes a Playwright browser instance and creates
    a toolkit with various web browsing and interaction tools.
    
    Returns:
        tuple: (tools_list, browser_instance, playwright_instance)
        
    Note:
        The browser is launched in non-headless mode for debugging purposes.
        In production, consider setting headless=True for better performance.
    """
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


def push(text: str):
    """
    Send a push notification to the user via Pushover.
    
    This function sends a text message to the user's devices through
    the Pushover notification service.
    
    Args:
        text: The message text to send
        
    Returns:
        str: "success" if the notification was sent successfully
        
    Note:
        Requires PUSHOVER_TOKEN and PUSHOVER_USER environment variables
        to be set for this function to work.
    """
    requests.post(pushover_url, data = {"token": pushover_token, "user": pushover_user, "message": text})
    return "success"


def get_file_tools():
    """
    Get file management tools for the sandbox directory.
    
    This function creates a file management toolkit that provides tools
    for reading, writing, and managing files in the sandbox directory.
    
    Returns:
        list: List of file management tools
        
    Note:
        All file operations are restricted to the "sandbox" directory
        for security purposes.
    """
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


async def other_tools():
    """
    Get all additional tools for the Sidekick assistant.
    
    This function creates and configures various tools including:
    - Push notification tool
    - File management tools
    - Web search tool
    - Wikipedia query tool
    - Python REPL tool
    
    Returns:
        list: Combined list of all available tools
        
    Note:
        Some tools require specific environment variables to function properly.
        Check the individual tool documentation for requirements.
    """
    push_tool = Tool(name="send_push_notification", func=push, description="Use this tool when you want to send a push notification")
    file_tools = get_file_tools()

    tool_search = Tool(
        name="search",
        func=serper.run,
        description="Use this tool when you want to get the results of an online web search"
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    python_repl = PythonREPLTool()
    
    return file_tools + [push_tool, tool_search, python_repl, wiki_tool]

