# server.py
from mcp.server.fastmcp import FastMCP
import asyncio

# Create an MCP server
mcp = FastMCP("document-generate")


# Add an addition tool
@mcp.tool()
async def markdown_generate(content: str, doc_name: str) -> str:
    """
    将文本以markdown形式保存在本地

    Args:
        content: 文件内容
        doc_name: 文件名字

    Returns:
        保存路径+文件文件名
    """

    save_path = "../doc/"

    if doc_name == "":
        return "without name"
    elif doc_name.endswith(".md") == False:
        doc_name += ".md"

    try:
        with open(save_path+doc_name,"w",encoding="utf-8") as md:
            md.write(content)
        return save_path+doc_name

    except Exception as e:
        return str(e)



if __name__ == "__main__":
    mcp.run(transport = "stdio")