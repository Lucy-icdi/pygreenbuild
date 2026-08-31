"""資料轉換 MCP tools。"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from pygreenbuild.api.services.transform import (
    fill_dataframe_na_service,
    fill_time_gaps_service,
    json_to_dataframe_service,
    pmv_ashrae_service,
    pmv_iso_service,
    to_date_column_service,
    to_datetime_column_service,
    to_time_column_service,
)


def register_transform_tools(mcp: FastMCP) -> None:
    """註冊資料轉換 tools。"""

    @mcp.tool()
    def json_to_dataframe(data: list[dict[str, Any]]) -> dict[str, Any]:
        """將 CODIS 觀測 JSON 轉為中文欄位 DataFrame（JSON records 格式）。"""
        return json_to_dataframe_service(data)

    @mcp.tool()
    def to_date_column(
        data: list[dict[str, Any]],
        column: str,
        result_col: str | None = None,
        as_string: bool = False,
    ) -> dict[str, Any]:
        """將指定欄位轉為純日期。"""
        return to_date_column_service(
            data, column, result_col=result_col, as_string=as_string
        )

    @mcp.tool()
    def to_time_column(
        data: list[dict[str, Any]],
        column: str,
        result_col: str | None = None,
        as_string: bool = False,
    ) -> dict[str, Any]:
        """將指定欄位轉為純時間（23:59 特殊處理）。"""
        return to_time_column_service(
            data, column, result_col=result_col, as_string=as_string
        )

    @mcp.tool()
    def to_datetime_column(
        data: list[dict[str, Any]],
        column: str,
        result_col: str | None = None,
        as_string: bool = False,
    ) -> dict[str, Any]:
        """將指定欄位轉為日期時間。"""
        return to_datetime_column_service(
            data, column, result_col=result_col, as_string=as_string
        )

    @mcp.tool()
    def fill_time_gaps(
        data: list[dict[str, Any]],
        datetime_col: str,
        freq: str,
        fill_method: str = "na",
        fill_value: object | None = None,
    ) -> dict[str, Any]:
        """依頻率補齊缺失時間列。

        Args:
            datetime_col: 日期時間欄位名稱。
            freq: pandas 頻率字串，例如 "h"、"3min"。
            fill_method: na/ffill/bfill/neighbor_mean/constant/median。
        """
        return fill_time_gaps_service(
            data,
            datetime_col,
            freq,
            fill_method=fill_method,  # type: ignore[arg-type]
            fill_value=fill_value,
        )

    @mcp.tool()
    def fill_dataframe_na(
        data: list[dict[str, Any]],
        range_col: str | None = None,
        range_start: Any = None,
        range_end: Any = None,
        exclude_cols: list[str] | None = None,
        fill_method: str = "neighbor_mean",
        fill_value: object | None = None,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """填補 DataFrame 中上下皆有值的孤立 NA。"""
        return fill_dataframe_na_service(
            data,
            range_col=range_col,
            range_start=range_start,
            range_end=range_end,
            exclude_cols=exclude_cols,
            fill_method=fill_method,  # type: ignore[arg-type]
            fill_value=fill_value,
            columns=columns,
        )

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
        return pmv_iso_service(
            tdb, tr, vr, rh, met, clo, wme,
            round_output=round_output,
            output=output,
        )

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
        return pmv_ashrae_service(
            tdb, tr, vr, rh, met, clo, wme,
            round_output=round_output,
            output=output,
        )
