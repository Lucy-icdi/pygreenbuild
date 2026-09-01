"""冰水主機 KPI MCP tools。"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from pygreenbuild.mcp.serialization import (
    dataframe_to_records,
    records_to_dataframe,
    wrap_success,
)
from pygreenbuild.metrics.chiller_performance import ChillerKPI
from pygreenbuild.metrics.chiller_usrt import calculatorUSRT


def register_metrics_tools(mcp: FastMCP) -> None:
    """註冊冰水主機 KPI tools。"""

    @mcp.tool()
    def chiller_usrt_single(
        flow_rate: float,
        flow_unit: str,
        return_temp: float,
        return_temp_unit: str,
        supply_temp: float,
        supply_temp_unit: str,
        kw_to_usrt: bool = True,
    ) -> dict[str, Any]:
        """計算單台冰水主機 USRT 或冷房 kW。"""
        result = calculatorUSRT.calculate_single_chiller_usrt(
            flow_rate=flow_rate,
            flow_unit=flow_unit,
            return_temp=return_temp,
            return_temp_unit=return_temp_unit,
            supply_temp=supply_temp,
            supply_temp_unit=supply_temp_unit,
            kw_to_usrt=kw_to_usrt,
        )
        return wrap_success(result)

    @mcp.tool()
    def chiller_usrt_zone_pumps(
        pumps: list[dict[str, Any]],
        kw_to_usrt: bool = True,
    ) -> dict[str, Any]:
        """聯合多區域泵計算總 USRT 或 kW。"""
        result = calculatorUSRT.zone_pumps_total(pumps, kw_to_usrt=kw_to_usrt)
        return wrap_success(result)

    @mcp.tool()
    def chiller_usrt_ice_melt(
        flow: float,
        hex_return_temp: float,
        hex_supply_temp: float,
        flow_unit: str = "CFM",
        temp_unit: str = "C",
        kw_to_usrt: bool = True,
    ) -> dict[str, Any]:
        """計算融冰 USRT。"""
        result = calculatorUSRT.ice_melt(
            flow,
            hex_return_temp,
            hex_supply_temp,
            flow_unit=flow_unit,
            temp_unit=temp_unit,
            kw_to_usrt=kw_to_usrt,
        )
        return wrap_success(result)

    @mcp.tool()
    def chiller_usrt_batch(
        data: list[dict[str, Any]],
        flow_col: str,
        return_temp_col: str,
        supply_temp_col: str,
        flow_unit: str = "CMH",
        return_temp_unit: str = "C",
        supply_temp_unit: str = "C",
        result_col: str = "USRT",
        kw_to_usrt: bool = True,
    ) -> dict[str, Any]:
        """批次計算 USRT。"""
        df = calculatorUSRT.calculate_usrts(
            records_to_dataframe(data),
            flow_col=flow_col,
            return_temp_col=return_temp_col,
            supply_temp_col=supply_temp_col,
            flow_unit=flow_unit,
            return_temp_unit=return_temp_unit,
            supply_temp_unit=supply_temp_unit,
            result_col=result_col,
            kw_to_usrt=kw_to_usrt,
        )
        return wrap_success(dataframe_to_records(df))

    @mcp.tool()
    def chiller_cop(cooling_kw: float, power_kw: float) -> dict[str, Any]:
        """計算 COP（冷房 kW / 功率 kW）。"""
        return wrap_success(ChillerKPI.calculate_cop(cooling_kw, power_kw))

    @mcp.tool()
    def chiller_eer(cooling_kw: float, power_kw: float) -> dict[str, Any]:
        """計算 EER（kcal/h/W）。"""
        return wrap_success(ChillerKPI.calculate_eer(cooling_kw, power_kw))

    @mcp.tool()
    def chiller_power_rate(
        power_kw: float,
        cooling_kw: float | None = None,
        usrt: float | None = None,
    ) -> dict[str, Any]:
        """計算耗電率（kW/USRT）。cooling_kw 與 usrt 擇一傳入。"""
        result = ChillerKPI.calculate_power_rate(
            power_kw, cooling_kw=cooling_kw, usrt=usrt
        )
        return wrap_success(result)

    @mcp.tool()
    def chiller_kw_to_usrt(cooling_kw: float) -> dict[str, Any]:
        """冷房 kW 轉 USRT（× 0.284）。"""
        return wrap_success(ChillerKPI.cooling_kw_to_usrt(cooling_kw))

    @mcp.tool()
    def chiller_performance_batch(
        data: list[dict[str, Any]],
        power_cols: list[str],
        cooling_kw_col: str = "冷房熱量_kW",
        cop_col: str = "COP",
        eer_col: str = "EER",
        power_rate_col: str = "耗電率",
        usrt_col: str | None = "USRT",
        power_rate_from: str = "cooling_kw",
        total_power_col: str | None = "輸入功率_kW",
    ) -> dict[str, Any]:
        """批次計算 COP、EER、USRT、耗電率。"""
        df = ChillerKPI.calculate_performance(
            records_to_dataframe(data),
            cooling_kw_col=cooling_kw_col,
            power_cols=power_cols,
            cop_col=cop_col,
            eer_col=eer_col,
            power_rate_col=power_rate_col,
            usrt_col=usrt_col,
            power_rate_from=power_rate_from,  # type: ignore[arg-type]
            total_power_col=total_power_col,
        )
        return wrap_success(dataframe_to_records(df))
