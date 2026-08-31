"""MCP tool 註冊模組。"""

from mcp.server.fastmcp import FastMCP

from .database import register_database_tools
from .load import register_load_tools
from .metrics import register_metrics_tools
from .transform import register_transform_tools
from .weather import register_weather_tools


def register_all_tools(mcp: FastMCP) -> None:
    """將所有領域 tools 註冊至同一 FastMCP 實例。

    Parameters
    ----------
    mcp :
        FastMCP 伺服器實例（單位：不適用）。
    """
    register_weather_tools(mcp)
    register_transform_tools(mcp)
    register_load_tools(mcp)
    register_metrics_tools(mcp)
    register_database_tools(mcp)
