"""pygreenbuild 統一 MCP Server 入口（FastMCP + stdio）。"""

from mcp.server.fastmcp import FastMCP

from pygreenbuild.mcp.tools import register_all_tools

mcp = FastMCP("pygreenbuild")
register_all_tools(mcp)


def main() -> None:
    """stdio 啟動入口，供 pyproject.toml console_scripts 呼叫。"""
    mcp.run()


if __name__ == "__main__":
    main()
