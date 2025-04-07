# server.py
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
import asyncio
import httpx

# Create an MCP server
mcp = FastMCP("web-search")


# Add an addition tool
@mcp.tool()
async def web_search(query: str) -> str:
    """
    搜索互联网内容

    Args:
        query: 要搜索内容

    Returns:
        搜索结果的总结
    """

    load_dotenv("../config/config.env")  # 加载配置文件

    web_base_url = os.getenv("web_url")
    web_api_key = os.getenv("web_api_key")
    web_name = os.getenv("web_name")

    # print(f"web_base_url: {web_base_url}\nweb_api_key: {web_api_key}\n")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            web_base_url,
            headers={
                'Authorization': "Bearer "+web_api_key,
                "Content-Type": "application/json"
            },
            json={
                "query": query,
                "topic": "general",
                "search_depth": "basic",
                "chunks_per_source": 3,
                "max_results":1,
                "time_range": None,
                "days": 3,
                "include_answer": True,
                "include_raw_content": False,
                "include_images": False,
                "include_image_descriptions": False,
                "include_domains": [],
                "exclude_domains": []
            }
        )

        if web_name == "tavily":
            return response.text
        else :
            return []


if __name__ == "__main__":
    mcp.run(transport = "stdio")
    # asyncio.run(web_search("苏州大学"))