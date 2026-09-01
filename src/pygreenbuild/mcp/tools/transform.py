"""資料轉換 MCP tools。"""

from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from pygreenbuild.mcp.serialization import (
    dataframe_to_records,
    records_to_dataframe,
    wrap_success,
)
from pygreenbuild.transform.fill_dataframe_na import (
    fill_dataframe_na as _fill_dataframe_na,
)
from pygreenbuild.transform.fill_time_gaps import fill_time_gaps as _fill_time_gaps
from pygreenbuild.transform.json_to_dataframe import (
    json_to_dataframe as _json_to_dataframe,
)
from pygreenbuild.transform.pmv import pmv_ashrae as _pmv_ashrae, pmv_iso as _pmv_iso
from pygreenbuild.transform.transform_time import (
    to_date_column as _to_date_column,
    to_datetime_column as _to_datetime_column,
    to_time_column as _to_time_column,
)

FillMethod = Literal[
    "na", "ffill", "bfill", "neighbor_mean", "constant", "median"
]


def register_transform_tools(mcp: FastMCP) -> None:
    """註冊資料轉換 tools。"""

    @mcp.tool()
    def json_to_dataframe(data: list[dict[str, Any]]) -> dict[str, Any]:
        """將 CODIS 觀測 JSON 轉為中文欄位 DataFrame（JSON records 格式）。"""
        df = _json_to_dataframe(data)
        return wrap_success(dataframe_to_records(df))

    @mcp.tool()
    def to_date_column(
        data: list[dict[str, Any]],
        column: str,
        result_col: str | None = None,
        as_string: bool = False,
    ) -> dict[str, Any]:
        """將指定欄位轉為純日期。"""
        df = _to_date_column(
            records_to_dataframe(data),
            column,
            result_col=result_col,
            as_string=as_string,
        )
        return wrap_success(dataframe_to_records(df))

    @mcp.tool()
    def to_time_column(
        data: list[dict[str, Any]],
        column: str,
        result_col: str | None = None,
        as_string: bool = False,
    ) -> dict[str, Any]:
        """將指定欄位轉為純時間（23:59 特殊處理）。"""
        df = _to_time_column(
            records_to_dataframe(data),
            column,
            result_col=result_col,
            as_string=as_string,
        )
        return wrap_success(dataframe_to_records(df))

    @mcp.tool()
    def to_datetime_column(
        data: list[dict[str, Any]],
        column: str,
        result_col: str | None = None,
        as_string: bool = False,
    ) -> dict[str, Any]:
        """將指定欄位轉為日期時間。"""
        df = _to_datetime_column(
            records_to_dataframe(data),
            column,
            result_col=result_col,
            as_string=as_string,
        )
        return wrap_success(dataframe_to_records(df))

    @mcp.tool()
    def fill_time_gaps(
        data: list[dict[str, Any]],
        datetime_col: str,
        freq: str,
        fill_method: FillMethod = "na",
        fill_value: object | None = None,
    ) -> dict[str, Any]:
        """依頻率補齊缺失時間列。

        Args:
            datetime_col: 日期時間欄位名稱。
            freq: pandas 頻率字串，例如 "h"、"3min"。
            fill_method: na/ffill/bfill/neighbor_mean/constant/median。
        """
        df = _fill_time_gaps(
            records_to_dataframe(data),
            datetime_col,
            freq,
            fill_method=fill_method,
            fill_value=fill_value,
        )
        return wrap_success(dataframe_to_records(df))

    @mcp.tool()
    def fill_dataframe_na(
        data: list[dict[str, Any]],
        range_col: str | None = None,
        range_start: Any = None,
        range_end: Any = None,
        exclude_cols: list[str] | None = None,
        fill_method: FillMethod = "neighbor_mean",
        fill_value: object | None = None,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """填補 DataFrame 中上下皆有值的孤立 NA。"""
        df = _fill_dataframe_na(
            records_to_dataframe(data),
            range_col=range_col,
            range_start=range_start,
            range_end=range_end,
            exclude_cols=exclude_cols,
            fill_method=fill_method,
            fill_value=fill_value,
            columns=columns,
        )
        return wrap_success(dataframe_to_records(df))

    @mcp.tool()
    def pmv_iso(
        tdb: float,
        tr: float,
        vr: float,
        rh: float,
        met: float,
        clo: float,
        wme: float = 0.0,
        round_output: bool = True,
        output: str = "all",
    ) -> dict[str, Any]:
        """計算 ISO 7730 PMV/PPD 熱舒適度。"""
        result = _pmv_iso(
            tdb,
            tr,
            vr,
            rh,
            met,
            clo,
            wme,
            round_output=round_output,
            output=output,  # type: ignore[arg-type]
        )
        return wrap_success(result)

    @mcp.tool()
    def pmv_ashrae(
        tdb: float,
        tr: float,
        vr: float,
        rh: float,
        met: float,
        clo: float,
        wme: float = 0.0,
        round_output: bool = True,
        output: str = "all",
    ) -> dict[str, Any]:
        """計算 ASHRAE 55 PMV/PPD 熱舒適度（含 Cooling Effect）。"""
        result = _pmv_ashrae(
            tdb,
            tr,
            vr,
            rh,
            met,
            clo,
            wme,
            round_output=round_output,
            output=output,  # type: ignore[arg-type]
        )
        return wrap_success(result)
