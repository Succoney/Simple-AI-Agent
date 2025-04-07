import asyncio
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
from openai import OpenAI
from dotenv import load_dotenv
import os
from typing import Optional
import json


class MCPClient:
    def __init__(self):
        load_dotenv("../config/config.env")
        self.exit_stack = AsyncExitStack()
        self.model = os.getenv("model")
        self.api_key = os.getenv("api_key")
        self.base_url = os.getenv("base_url")
        self.client = OpenAI(api_key = self.api_key,base_url = self.base_url)
        self.session : List[ClientSession] = []
        self.toolid = dict()


    async def web_search(self, query : str) -> list[dict]:
        pass


    async def process_query(self, messages : list[dict]) -> list[dict]:
        """
        使用大模型处理查询并调用可用的 MCP 工具 (Function Calling)
        """

        available_tools = []
        query = messages[0]["content"]

        for index, session in enumerate(self.session):
            responce = await session.list_tools()

            server_available_tools = [{
                "type" : "function",
                "function" : {
                    "name" : tool.name,
                    "description" : tool.description,
                    "input_schema" : tool.inputSchema
                }
            } for tool in responce.tools]

            for tool in responce.tools:
                self.toolid[tool.name] = index

            available_tools += server_available_tools

        try:
            if query == "file upload":
                result = await self.session[self.toolid["file_upload"]].call_tool("file_upload")
                query = input("File upload successfully! Query about the file: ").strip()
                messages+=[{
                        "role": "user",
                        "content": result.content[0].text,
                    },{
                        "role": "user",
                        "content": query
                    }]
                

                response = self.client.chat.completions.create(
                    model = self.model,
                    messages = messages,
                )

                return response.choices[0].message.content

            elif query == "image upload":
                result = await self.session[self.toolid["image_upload"]].call_tool("image_upload")
                query = input("File upload successfully! Query about the file: ").strip()
                messages+=[{
                        "role": "user",
                        "content": result.content[0].text,
                    },{
                        "role": "user",
                        "content": query
                    }]
                

                response = self.client.chat.completions.create(
                    model = self.model,
                    messages = messages,
                )

                return response.choices[0].message.content
                
            else:

                response = self.client.chat.completions.create(
                        model = self.model,
                        messages = messages,
                        tools = available_tools
                    )


                messages = [messages[-1]]

                content = response.choices[0]

                if content.finish_reason == "tool_calls":
                    # 如果是需要使用工具就解析工具
                    tool_call = content.message.tool_calls[0]
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    print(f"\n[Calling tool {tool_name} with args {tool_args}]")

                    # 执行工具
                    result = await self.session[self.toolid[tool_name]].call_tool(tool_name,tool_args)

                    messages.append(content.message.model_dump())

                    messages.append({
                        "role" : "tool",
                        "content" : result.content[0].text,
                        "tool_call_id" : tool_call.id,
                    })

                    # 将工具调用结果放到messages中

                    return messages
                else:

                    messages.append({
                        "role" : "assistant",
                        "content" : response.choices[0].message.content,
                    })
                    
                    return messages
        except Exception as e:
            return f"错误信息：{str(e)}"


    async def connect_to_mock_server(self, server_script_path: str):
        "模拟 mcp 服务器的连接"
        print(" mcp 客户端已完成初始化, 准备连接服务器")
        if_python = server_script_path.endswith(".py")
        if_js = server_script_path.endswith(".js")

        if not if_python and not if_js:
            raise ValueError("服务器脚本必须是 .py 或者 .js 文件")

        command = "python" if if_python else "node"

        # 设置标准输入输出通信的参数
        server_params = StdioServerParameters(
            command = command,
            args = [server_script_path],
            env = None
        )

        # 启动 MCP 并建立通信
        # exit_stack是contextlib创建的对象,用于管理多个异步上下文管理器。
        # enter_async_context 进入一个异步上下文管理器，并返回该管理器
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params)) # 创建一个标准io通信
        self.stdio, self.write = stdio_transport
        session = await self.exit_stack.enter_async_context(ClientSession(self.stdio,self.write)) # 创建一个客户端会话

        await session.initialize() # 会话初始化

        # 列出 MCP 服务器上的工具
        response = await session.list_tools() # 列出服务器的工具
        tools = response.tools
        print("\n以连接到服务器,支持一下工具:",[tool for tool in tools])
        self.session.append(session)



    async def loop_chat(self) -> str:
        "运行交互式聊天循环"
        print("\n MCP 客户端已启动!")
        try:
            while(True):
                query = input("Query: ").strip()

                if query == "":
                    print("You don't input any query, please give me some query。🥺🥺🥺")
                    continue

                if "quit()" in query.lower():
                    break
                else:
                    messages = [{
                        "role" : "user",
                        "content" : query,
                    }]
                    response = await self.process_query(messages)
                    print(response)
        except Exception as e:
            return str(e)

    async def cleanup(self):
        await self.exit_stack.aclose()

async def main():
    
    if len(sys.argv) < 2:
        print("Usage: python mcp_client.py <path_to_server_script>")
        sys.exit(1)
    client = MCPClient()
    try:
        for i in range(1,len(sys.argv)):
            await client.connect_to_mock_server(sys.argv[i])
        await client.loop_chat()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())