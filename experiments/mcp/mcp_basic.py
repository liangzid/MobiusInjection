"""
第一个MCP Server - 简单示例
学习用：如何定义tool
"""

from mcp.server.fastmcp import FastMCP

# 创建MCP Server
mcp = FastMCP("SimpleServer")

# 定义一个tool（工具）
@mcp.tool()
def add(a: int, b: int) -> int:
    """计算两个数的和"""
    return a + b

@mcp.tool()
def read_file(path: str) -> str:
    """读取文件内容"""
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

# 运行服务器
if __name__ == "__main__":
    mcp.run()
