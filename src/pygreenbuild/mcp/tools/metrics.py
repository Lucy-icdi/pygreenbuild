"""冰水主機 KPI MCP tools。"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from pygreenbuild.api.services.metrics import (
    chiller_cop_service,
    chiller_eer_service,
    chiller_kw_to_usrt_service,
    chiller_performance_batch_service,
    chiller_power_rate_service,
    chiller_usrt_batch_service,
    chiller_usrt_ice_melt_service,
    chiller_usrt_single_service,
    chiller_usrt_zone_pumps_service,
)


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
        return chiller_usrt_single_service(
            flow_rate,
            flow_unit,
            return_temp,
            return_temp_unit,
            supply_temp,
            supply_temp_unit,
            kw_to_usrt=kw_to_usrt,
        )

    @mcp.tool()
    def chiller_usrt_zone_pumps(
        pumps: list[dict[str, Any]],
        kw_to_usrt: bool = True,
    ) -> dict[str, Any]:
        """聯合多區域泵計算總 USRT 或 kW。"""
        return chiller_usrt_zone_pumps_service(pumps, kw_to_usrt=kw_to_usrt)

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
        return chiller_usrt_ice_melt_service(
            flow,
            hex_return_temp,
            hex_supply_temp,
            flow_unit=flow_unit,
            temp_unit=temp_unit,
            kw_to_usrt=kw_to_usrt,
        )

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
        return chiller_usrt_batch_service(
            data,
            flow_col=flow_col,
            return_temp_col=return_temp_col,
            supply_temp_col=supply_temp_col,
            flow_unit=flow_unit,
            return_temp_unit=return_temp_unit,
            supply_temp_unit=supply_temp_unit,
            result_col=result_col,
            kw_to_usrt=kw_to_usrt,
        )

    @mcp.tool()
    def chiller_cop(cooling_kw: float, power_kw: float) -> dict[str, Any]:
        """計算 COP（冷房 kW / 功率 kW）。"""
        return chiller_cop_service(cooling_kw, power_kw)

    @mcp.tool()
    def chiller_eer(cooling_kw: float, power_kw: float) -> dict[str, Any]:
        """計算 EER（kcal/h/W）。"""
        return chiller_eer_service(cooling_kw, power_kw)

    @mcp.tool()
    def chiller_power_rate(
        power_kw: float,
        cooling_kw: float | None = None,
        usrt: float | None = None,
    ) -> dict[str, Any]:
        """計算耗電率（kW/USRT）。cooling_kw 與 usrt 擇一傳入。"""
        return chiller_power_rate_service(
            power_kw, cooling_kw=cooling_kw, usrt=usrt
        )

    @mcp.tool()
    def chiller_kw_to_usrt(cooling_kw: float) -> dict[str, Any]:
        """冷房 kW 轉 USRT（× 0.284）。"""
        return chiller_kw_to_usrt_service(cooling_kw)

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
        return chiller_performance_batch_service(
            data,
            cooling_kw_col=cooling_kw_col,
            power_cols=power_cols,
            cop_col=cop_col,
            eer_col=eer_col,
            power_rate_col=power_rate_col,
            usrt_col=usrt_col,
            power_rate_from=power_rate_from,
            total_power_col=total_power_col,
        )
