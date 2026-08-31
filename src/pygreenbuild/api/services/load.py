"""資料合併服務層。"""

from __future__ import annotations

from typing import Any

from pygreenbuild.api.serialization import dataframes_dict_to_records, wrap_success
from pygreenbuild.load.codis_data_merge import (
    codis_day_merge,
    codis_hour_merge,
    codis_merge,
    codis_month_merge,
)


def _merge_service(
    merge_fn,
    base_path: str,
    *,
    station_ids: list[str] | None = None,
    pattern: str | None = None,
) -> dict[str, Any]:
    """共用 CODIS 合併邏輯，MCP 模式不寫 CSV。"""
    results = merge_fn(
        base_path,
        output_dir=None,
        station_ids=station_ids,
        pattern=pattern,
        to_csv=False,
    )
    return wrap_success(dataframes_dict_to_records(results))


def codis_merge_service(
    base_path: str,
    *,
    station_ids: list[str] | None = None,
    pattern: str | None = None,
) -> dict[str, Any]:
    """合併 CODIS 測站 JSON 資料。"""
    return _merge_service(codis_merge, base_path, station_ids=station_ids, pattern=pattern)


def codis_hour_merge_service(
    base_path: str,
    *,
    station_ids: list[str] | None = None,
    pattern: str | None = None,
) -> dict[str, Any]:
    """合併 CODIS 小時資料。"""
    return _merge_service(
        codis_hour_merge, base_path, station_ids=station_ids, pattern=pattern
    )


def codis_day_merge_service(
    base_path: str,
    *,
    station_ids: list[str] | None = None,
    pattern: str | None = None,
) -> dict[str, Any]:
    """合併 CODIS 日資料。"""
    return _merge_service(
        codis_day_merge, base_path, station_ids=station_ids, pattern=pattern
    )


def codis_month_merge_service(
    base_path: str,
    *,
    station_ids: list[str] | None = None,
    pattern: str | None = None,
) -> dict[str, Any]:
    """合併 CODIS 月資料。"""
    return _merge_service(
        codis_month_merge, base_path, station_ids=station_ids, pattern=pattern
    )
