"""天氣擷取 MCP tools。"""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from pygreenbuild.ingestion.weather_crawler.codis_stn_obs_crawler import (
    codis_daily as _codis_daily,
    codis_monthly as _codis_monthly,
    codis_yearly as _codis_yearly,
)
from pygreenbuild.ingestion.weather_crawler.codis_single_item_crawler import (
    codis_single_daily_yearly as _codis_single_daily_yearly,
    codis_single_hourly_monthly as _codis_single_hourly_monthly,
    codis_single_monthly_yearly as _codis_single_monthly_yearly,
)
from pygreenbuild.ingestion.weather_crawler.cwa_township_forecast import (
    cwa_township_forecast_3day as _cwa_township_forecast_3day,
    cwa_township_forecast_week as _cwa_township_forecast_week,
)
from pygreenbuild.mcp.serialization import wrap_failure, wrap_success


def _resolve_cwa_api_key(api_key: str | None) -> str | None:
    """從參數或 ``CWA_API_KEY`` 環境變數取得授權碼。"""
    if api_key:
        return api_key
    return os.environ.get("CWA_API_KEY")


def register_weather_tools(mcp: FastMCP) -> None:
    """註冊天氣擷取 tools。"""

    @mcp.tool()
    def codis_daily(station_id: str, dates: list[str]) -> dict[str, Any]:
        """下載 CODIS 日報觀測 JSON。

        Args:
            station_id: 測站代碼，例如 "466920"。
            dates: 日期列表 (YYYY-MM-DD)；多日期時間隔不得超過 31 天。
        """
        if not dates:
            return wrap_failure("dates 不可為空")
        success, data, message = _codis_daily(
            station_id,
            None,
            *dates,
            return_data=True,
        )
        if not success or data is None:
            return wrap_failure(message)
        return wrap_success(data, message=message)

    @mcp.tool()
    def codis_monthly(station_id: str, year_month: str) -> dict[str, Any]:
        """下載 CODIS 月報觀測 JSON。

        Args:
            station_id: 測站代碼。
            year_month: 年月，格式 YYYYMM、YYYY-MM 或 YYYY-MM-DD。
        """
        success, data, message = _codis_monthly(
            station_id,
            None,
            year_month,
            return_data=True,
        )
        if not success or data is None:
            return wrap_failure(message)
        return wrap_success(data, message=message)

    @mcp.tool()
    def codis_yearly(station_id: str, year: str) -> dict[str, Any]:
        """下載 CODIS 年報觀測 JSON。

        Args:
            station_id: 測站代碼。
            year: 年份，例如 "2024"。
        """
        success, data, message = _codis_yearly(
            station_id,
            None,
            year,
            return_data=True,
        )
        if not success or data is None:
            return wrap_failure(message)
        return wrap_success(data, message=message)

    @mcp.tool()
    def codis_single_hourly_monthly(
        station_id: str,
        year_month: str,
        item: str,
        match_index: int = 1,
    ) -> dict[str, Any]:
        """下載 CODIS 單項逐時月報表 JSON。

        Args:
            station_id: 測站代碼，例如 "466900"。
            year_month: 年月，格式 YYYYMM、YYYY-MM 或 YYYY-MM-DD。
            item: 觀測要素中文名稱（可正則模糊比對）或英文 API 代碼。
            match_index: 多個 key 匹配時選用第幾個（從 1 起算），預設 1。
        """
        success, data, message = _codis_single_hourly_monthly(
            station_id,
            year_month,
            item,
            match_index,
        )
        if not success or data is None:
            return wrap_failure(message)
        return wrap_success(data, message=message)

    @mcp.tool()
    def codis_single_daily_yearly(
        station_id: str,
        year: str,
        item: str,
        match_index: int = 1,
    ) -> dict[str, Any]:
        """下載 CODIS 單項逐日年報表 JSON。

        Args:
            station_id: 測站代碼，例如 "466930"。
            year: 年份，格式 YYYY、YYYYMM、YYYY-MM 或 YYYY-MM-DD。
            item: 觀測要素中文名稱（可正則模糊比對）或英文 API 代碼。
            match_index: 多個 key 匹配時選用第幾個（從 1 起算），預設 1。
        """
        success, data, message = _codis_single_daily_yearly(
            station_id,
            year,
            item,
            match_index,
        )
        if not success or data is None:
            return wrap_failure(message)
        return wrap_success(data, message=message)

    @mcp.tool()
    def codis_single_monthly_yearly(
        station_id: str,
        year: str,
        item: str,
        match_index: int = 1,
    ) -> dict[str, Any]:
        """下載 CODIS 單項逐月年報表 JSON。

        Args:
            station_id: 測站代碼，例如 "466930"。
            year: 年份，格式 YYYY、YYYYMM、YYYY-MM 或 YYYY-MM-DD。
            item: 觀測要素中文名稱（可正則模糊比對）或英文 API 代碼。
            match_index: 多個 key 匹配時選用第幾個（從 1 起算），預設 1。
        """
        success, data, message = _codis_single_monthly_yearly(
            station_id,
            year,
            item,
            match_index,
        )
        if not success or data is None:
            return wrap_failure(message)
        return wrap_success(data, message=message)

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
        resolved_key = _resolve_cwa_api_key(api_key)
        if not resolved_key:
            return wrap_failure("需提供 api_key 或設定 CWA_API_KEY 環境變數")

        county_args = tuple(counties) if counties else ()
        success, data, message = _cwa_township_forecast_3day(
            resolved_key,
            None,
            *county_args,
            return_data=True,
        )
        if data is None:
            return wrap_failure(message)
        return {"success": success, "message": message, "result": data}

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
        resolved_key = _resolve_cwa_api_key(api_key)
        if not resolved_key:
            return wrap_failure("需提供 api_key 或設定 CWA_API_KEY 環境變數")

        county_args = tuple(counties) if counties else ()
        success, data, message = _cwa_township_forecast_week(
            resolved_key,
            None,
            *county_args,
            return_data=True,
        )
        if data is None:
            return wrap_failure(message)
        return {"success": success, "message": message, "result": data}
