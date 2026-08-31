"""天氣擷取 MCP tools。"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from pygreenbuild.api.services.weather import (
    codis_daily_service,
    codis_monthly_service,
    codis_yearly_service,
    cwa_township_forecast_3day_service,
    cwa_township_forecast_week_service,
)


def register_weather_tools(mcp: FastMCP) -> None:
    """註冊天氣擷取 tools。"""

    @mcp.tool()
    def codis_daily(station_id: str, dates: list[str]) -> dict[str, Any]:
        """下載 CODIS 日報觀測 JSON。

        Args:
            station_id: 測站代碼，例如 "466920"。
            dates: 日期列表 (YYYY-MM-DD)；多日期時間隔不得超過 31 天。
        """
        return codis_daily_service(station_id, dates)

    @mcp.tool()
    def codis_monthly(station_id: str, year_month: str) -> dict[str, Any]:
        """下載 CODIS 月報觀測 JSON。

        Args:
            station_id: 測站代碼。
            year_month: 年月，格式 YYYYMM、YYYY-MM 或 YYYY-MM-DD。
        """
        return codis_monthly_service(station_id, year_month)

    @mcp.tool()
    def codis_yearly(station_id: str, year: str) -> dict[str, Any]:
        """下載 CODIS 年報觀測 JSON。

        Args:
            station_id: 測站代碼。
            year: 年份，例如 "2024"。
        """
        return codis_yearly_service(station_id, year)

    @mcp.tool()
    def cwa_township_forecast_3day(
        counties: list[str] | None = None,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """下載 CWA 鄉鎮 3 天預報（逐 3 小時）。

        Args:
            counties: 縣市名稱或資料編號列表；省略則批次 22 縣市。
            api_key: CWA OpenData 授權碼；省略時讀取 CWA_API_KEY 環境變數。
        """
        return cwa_township_forecast_3day_service(counties, api_key)

    @mcp.tool()
    def cwa_township_forecast_week(
        counties: list[str] | None = None,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """下載 CWA 鄉鎮 1 週預報。

        Args:
            counties: 縣市名稱或資料編號列表；省略則批次 22 縣市。
            api_key: CWA OpenData 授權碼；省略時讀取 CWA_API_KEY 環境變數。
        """
        return cwa_township_forecast_week_service(counties, api_key)
