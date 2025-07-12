# Sidekick Personal Co-Worker

A powerful AI assistant built with LangGraph that can perform complex tasks using multiple tools and provides intelligent feedback on task completion.

## Overview

Sidekick is an intelligent AI assistant that combines the power of LangGraph, OpenAI's GPT models, and various tools to help you complete tasks efficiently. It features a sophisticated evaluation system that ensures tasks are completed according to your specified success criteria.

## Features

### 🤖 **Intelligent Task Processing**
- Uses GPT-4o-mini for natural language understanding and task execution
- Implements a worker-evaluator pattern for continuous improvement
- Automatically retries tasks until success criteria are met

### 🛠️ **Comprehensive Toolset**
- **Web Browsing**: Navigate and interact with web pages using Playwright
- **File Management**: Create, read, and manage files in a sandbox environment
- **Web Search**: Search the internet using Google Serper API
- **Wikipedia**: Access Wikipedia information
- **Python Code Execution**: Run Python code in a REPL environment
- **Push Notifications**: Send notifications via Pushover

### 📊 **Smart Evaluation System**
- Evaluates task completion against user-defined success criteria
- Provides detailed feedback on responses
- Determines when user input is needed for clarification
- Prevents infinite loops by detecting stuck states

### 🎨 **User-Friendly Interface**
- Clean Gradio web interface
- Real-time chat interaction
- Configurable success criteria
- Easy reset functionality

## Architecture

The Sidekick app uses a sophisticated graph-based architecture:

```
START → Worker → Router → Tools/Evaluator → END
```

1. **Worker Node**: Processes user requests using LLM and tools
2. **Router**: Determines whether to use tools or evaluate the response
3. **Tools Node**: Executes various tools (web browsing, file operations, etc.)
4. **Evaluator Node**: Assesses if success criteria are met
5. **Feedback Loop**: Continues until task completion or user input needed

## Prerequisites

- Python 3.8+
- OpenAI API key
- Google Serper API key (optional, for web search)
- Pushover credentials (optional, for notifications)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd langgraph-examples/sidekick-app
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   SERPER_API_KEY=your_serper_api_key_here  # Optional
   PUSHOVER_TOKEN=your_pushover_token_here  # Optional
   PUSHOVER_USER=your_pushover_user_here    # Optional
   ```

## Usage

### Starting the Application

Run the main application:
```bash
python app.py
```

The web interface will open automatically in your browser at `http://localhost:7860`.

### Using Sidekick

1. **Enter your request** in the message box
2. **Define success criteria** to specify what constitutes a successful completion
3. **Click "Go!"** or press Enter to start processing
4. **Monitor the conversation** as Sidekick works on your task
5. **Review feedback** from the evaluator system

### Example Usage

**Request**: "Research the latest developments in quantum computing and create a summary report"

**Success Criteria**: "Provide a comprehensive summary of recent quantum computing breakthroughs, including at least 3 major developments from the past year, and save the report as a markdown file"

Sidekick will:
1. Search for quantum computing information
2. Browse relevant web pages
3. Compile the information
4. Create a markdown report
5. Evaluate if the criteria are met
6. Provide feedback on the completion

## Configuration

### Customizing Tools

You can modify the available tools by editing `sidekick_tools.py`:

- Add new API integrations
- Modify existing tool configurations
- Add custom tools for specific use cases

### Adjusting Evaluation Criteria

The evaluator system can be customized in `sidekick.py` by modifying the `EvaluatorOutput` model and evaluation prompts.

## File Structure

```
sidekick-app/
├── app.py              # Gradio web interface
├── sidekick.py         # Core Sidekick implementation
├── sidekick_tools.py   # Tool definitions and configurations
├── README.md          # This file
├── requirements.txt   # Python dependencies
└── sandbox/          # File management workspace
```

## Key Components

### `app.py`
- Gradio web interface
- State management for the Sidekick instance
- User interaction handling

### `sidekick.py`
- Core Sidekick class implementation
- LangGraph workflow definition
- Worker and evaluator nodes
- State management and memory

### `sidekick_tools.py`
- Tool definitions and configurations
- Playwright browser setup
- API integrations (search, notifications, etc.)

## Troubleshooting

### Common Issues

1. **Browser not launching**: Ensure Playwright is properly installed
   ```bash
   playwright install chromium
   ```

2. **API key errors**: Verify your environment variables are set correctly

3. **Memory issues**: The app uses memory checkpoints; reset if needed

### Performance Tips

- Use specific success criteria for better task completion
- Provide clear, detailed requests
- Monitor the feedback system for optimization opportunities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Powered by [OpenAI GPT models](https://openai.com/)
- Web interface by [Gradio](https://gradio.app/)
- Browser automation with [Playwright](https://playwright.dev/) 