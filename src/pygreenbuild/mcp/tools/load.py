"""資料合併 MCP tools。"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from pygreenbuild.api.services.load import (
    codis_day_merge_service,
    codis_hour_merge_service,
    codis_merge_service,
    codis_month_merge_service,
)


def register_load_tools(mcp: FastMCP) -> None:
    """註冊 CODIS 合併 tools。"""

    @mcp.tool()
    def codis_merge(
        base_path: str,
        station_ids: list[str] | None = None,
        pattern: str | None = None,
    ) -> dict[str, Any]:
        """合併 CODIS 測站 JSON 資料為 DataFrame（JSON records 格式）。"""
        return codis_merge_service(base_path, station_ids=station_ids, pattern=pattern)

    @mcp.tool()
    def codis_hour_merge(
        base_path: str,
        station_ids: list[str] | None = None,
        pattern: str | None = None,
    ) -> dict[str, Any]:
        """合併 CODIS 小時資料。"""
        return codis_hour_merge_service(
            base_path, station_ids=station_ids, pattern=pattern
        )

    @mcp.tool()
    def codis_day_merge(
        base_path: str,
        station_ids: list[str] | None = None,
        pattern: str | None = None,
    ) -> dict[str, Any]:
        """合併 CODIS 日資料。"""
        return codis_day_merge_service(
            base_path, station_ids=station_ids, pattern=pattern
        )

    @mcp.tool()
    def codis_month_merge(
        base_path: str,
        station_ids: list[str] | None = None,
        pattern: str | None = None,
    ) -> dict[str, Any]:
        """合併 CODIS 月資料。"""
        return codis_month_merge_service(
            base_path, station_ids=station_ids, pattern=pattern
        )
