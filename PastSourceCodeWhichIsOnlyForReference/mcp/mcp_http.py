"""
MCP Server with HTTP transport
==============================
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("TestServer")

call_count = {}

@mcp.tool()
def get_data(key: str) -> dict:
    global call_count
    if key not in call_count:
        call_count[key] = 0
    call_count[key] += 1
    n = call_count[key]

    if n < 5:
        return {
            "data": f"value_{n}",
            "next_action": f"call get_data again to verify (round {n})"
        }
    else:
        return {
            "data": f"value_{n}",
            "next_action": "done"
        }

@mcp.tool()
def get_count() -> dict:
    return {"count": call_count}

if __name__ == "__main__":
    # Use streamable-http transport on port 8080
    mcp.run(transport="streamable-http", mount_path="/mcp")
