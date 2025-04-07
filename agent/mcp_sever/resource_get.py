# server.py
from mcp.server.fastmcp import FastMCP, Image
from PIL import Image as PILImage
import pytesseract
import os
import asyncio
import tkinter as tk
from tkinter import filedialog

# Create an MCP server
mcp = FastMCP("resource")


# Add an addition tool
@mcp.tool()
async def file_upload() -> str:
    """
    上传本地文件

    Args:
        无

    Returns:
        本地文件内容
    """

    # 创建隐藏的主窗口（tkinter 要求）
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 弹出文件选择对话框
    file_path = filedialog.askopenfilename(
        title="选择文件",
        filetypes=[("所有文件", "*.*")]
    )
    
    if not file_path:  # 用户取消选择
        # print("未选择文件")
        return ""

    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        # print("文件内容:\n", content)
        return content

    except Exception as e:
        # print("读取文件失败:", e)
        return str(e)


@mcp.tool()
async def image_upload() -> str:
    """
    上传本地图片

    Args:
        无

    Returns:
        本地文件内容
    """

    # 创建隐藏的主窗口（tkinter 要求）
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 弹出文件选择对话框
    image_path = filedialog.askopenfilename(
        title="选择文件",
        filetypes=[("png文件", "*.png")]
    )
    
    if not image_path:  # 用户取消选择
        # print("未选择")
        return ""

    # 读取文件内容
    try:
        img = PILImage.open(image_path)
        img.thumbnail((100, 100))
        text = pytesseract.image_to_string(img)
        return text

    except Exception as e:
        # print("读取文件失败:", e)
        return str(e)




if __name__ == "__main__":
    mcp.run(transport = "stdio")