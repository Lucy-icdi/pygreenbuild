"""天氣擷取服務層。"""

from __future__ import annotations

import os
from typing import Any

from pygreenbuild.api.serialization import wrap_failure, wrap_success
from pygreenbuild.ingestion.weather_crawler.codis_crawler_tojson import (
    codis_daily,
    codis_monthly,
    codis_yearly,
)
from pygreenbuild.ingestion.weather_crawler.cwa_township_forecast import (
    cwa_township_forecast_3day,
    cwa_township_forecast_week,
)


def _resolve_cwa_api_key(api_key: str | None) -> str | None:
    """從參數或環境變數取得 CWA API Key。"""
    if api_key:
        return api_key
    return os.environ.get("CWA_API_KEY")


def codis_daily_service(
    station_id: str,
    dates: list[str],
) -> dict[str, Any]:
    """下載 CODIS 日報並回傳 JSON 資料。

    Parameters
    ----------
    station_id :
        測站代碼（單位：不適用）。
    dates :
        日期列表，格式 ``YYYY-MM-DD``；多日期時間隔不得超過 31 天（單位：不適用）。

    Returns
    -------
    dict[str, Any]
        含 ``success``、``message``、``result``（JSON list）（單位：不適用）。
    """
    if not dates:
        return wrap_failure("dates 不可為空")
    success, data, message = codis_daily(
        station_id,
        None,
        *dates,
        return_data=True,
    )
    if not success or data is None:
        return wrap_failure(message)
    return wrap_success(data, message=message)


def codis_monthly_service(
    station_id: str,
    year_month: str,
) -> dict[str, Any]:
    """下載 CODIS 月報並回傳 JSON 資料。"""
    success, data, message = codis_monthly(
        station_id,
        None,
        year_month,
        return_data=True,
    )
    if not success or data is None:
        return wrap_failure(message)
    return wrap_success(data, message=message)


def codis_yearly_service(
    station_id: str,
    year: str | int,
) -> dict[str, Any]:
    """下載 CODIS 年報並回傳 JSON 資料。"""
    success, data, message = codis_yearly(
        station_id,
        None,
        year,
        return_data=True,
    )
    if not success or data is None:
        return wrap_failure(message)
    return wrap_success(data, message=message)


def cwa_township_forecast_3day_service(
    counties: list[str] | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """下載 CWA 鄉鎮 3 天預報。"""
    resolved_key = _resolve_cwa_api_key(api_key)
    if not resolved_key:
        return wrap_failure("需提供 api_key 或設定 CWA_API_KEY 環境變數")

    county_args = tuple(counties) if counties else ()
    success, data, message = cwa_township_forecast_3day(
        resolved_key,
        None,
        *county_args,
        return_data=True,
    )
    if data is None:
        return wrap_failure(message)
    return {"success": success, "message": message, "result": data}


def cwa_township_forecast_week_service(
    counties: list[str] | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """下載 CWA 鄉鎮 1 週預報。"""
    resolved_key = _resolve_cwa_api_key(api_key)
    if not resolved_key:
        return wrap_failure("需提供 api_key 或設定 CWA_API_KEY 環境變數")

    county_args = tuple(counties) if counties else ()
    success, data, message = cwa_township_forecast_week(
        resolved_key,
        None,
        *county_args,
        return_data=True,
    )
    if data is None:
        return wrap_failure(message)
    return {"success": success, "message": message, "result": data}
