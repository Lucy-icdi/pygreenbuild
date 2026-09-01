"""資料合併 MCP tools。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp import FastMCP

from pygreenbuild.load.codis_data_merge import (
    codis_day_merge as _codis_day_merge,
    codis_hour_merge as _codis_hour_merge,
    codis_merge as _codis_merge,
    codis_month_merge as _codis_month_merge,
)
from pygreenbuild.mcp.serialization import dataframes_dict_to_records, wrap_success


def _merge(
    merge_fn: Callable[..., dict],
    base_path: str,
    *,
    station_ids: list[str] | None,
    pattern: str | None,
) -> dict[str, Any]:
    """呼叫 CODIS 合併函式，MCP 模式不寫 CSV。"""
    results = merge_fn(
        base_path,
        output_dir=None,
        station_ids=station_ids,
        pattern=pattern,
        to_csv=False,
    )
    return wrap_success(dataframes_dict_to_records(results))


def register_load_tools(mcp: FastMCP) -> None:
    """註冊 CODIS 合併 tools。"""

    @mcp.tool()
    def codis_merge(
        base_path: str,
        station_ids: list[str] | None = None,
        pattern: str | None = None,
    ) -> dict[str, Any]:
        """合併 CODIS 測站 JSON 資料為 DataFrame（JSON records 格式）。"""
        return _merge(
            _codis_merge, base_path, station_ids=station_ids, pattern=pattern
        )

    @mcp.tool()
    def codis_hour_merge(
        base_path: str,
        station_ids: list[str] | None = None,
        pattern: str | None = None,
    ) -> dict[str, Any]:
        """合併 CODIS 小時資料。"""
        return _merge(
            _codis_hour_merge, base_path, station_ids=station_ids, pattern=pattern
        )

    @mcp.tool()
    def codis_day_merge(
        base_path: str,
        station_ids: list[str] | None = None,
        pattern: str | None = None,
    ) -> dict[str, Any]:
        """合併 CODIS 日資料。"""
        return _merge(
            _codis_day_merge, base_path, station_ids=station_ids, pattern=pattern
        )

    @mcp.tool()
    def codis_month_merge(
        base_path: str,
        station_ids: list[str] | None = None,
        pattern: str | None = None,
    ) -> dict[str, Any]:
        """合併 CODIS 月資料。"""
        return _merge(
            _codis_month_merge, base_path, station_ids=station_ids, pattern=pattern
        )
