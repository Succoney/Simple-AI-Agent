# Simple AI Agent

## Features

This AI agent is capable of **automatic task decomposition**, **step-by-step problem solving**, **web search**, and **file generation**.

The web search and file generation features are powered by **MCP (Model Context Protocol)** technology.

As a user (or "boss"), you can assign a task to the AI agent. The agent will automatically break it down into multiple steps and execute them one by one. If any step goes beyond the capabilities of the language model itself, the model will send a request to the MCP server via the MCP client. The server will select the appropriate tool and return the result.

### Currently implemented features:
- Web search  
- Markdown file generation  
- File upload  

Planned features include:
- Terminal command execution  
- Code writing and execution  
- Browser control  

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/Succoney/Simple-AI-Agent.git
   cd Simple-AI-Agent/
   ```

2. Create and activate the environment:
   ```bash
   conda create -n simple-agent python=3.12
   conda activate simple-agent
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt

   # If the installation fails, try:
   python -m pip install -r requirements.txt
   ```

4. Configure model and web search API settings:  
   Edit the `./config/config.env` file with your model name, base URL, API key, and web search API info.

5. Start the AI agent:
   ```bash
   cd agent/
   sh run_agent.sh
   ```

## Demo

[![Demo Video](/img/video.webp)](https://www.bilibili.com/video/BV1d5dJY8E4n?t=10.3)
