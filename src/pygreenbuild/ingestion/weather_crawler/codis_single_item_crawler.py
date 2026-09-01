"""CODIS 單項天氣參數下載。

目前實作：
- 單項逐時月報表（API type: ``one_date``）
- 單項逐日年報表（API type: ``one_month``）
- 單項逐月年報表（API type: ``one_year``）

觀測要素可傳入中文 key（正則模糊比對）或英文 value。
"""

from __future__ import annotations

import calendar
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests

from .codis_cookie_manager import get_valid_cookie
from .codis_stn_obs_crawler import (
    API_URL,
    HEADERS,
    CodisData,
    _get_stn_type,
    _parse_year_month,
    _save_json,
)

# 對照表來自 參考資料/Codis/codis_single_item_mapping.json
# one_date：單項逐時月報表
ONE_DATE_ITEMS: Dict[str, str] = {
    "測站氣壓(hPa)": "StationPressure",
    "海平面氣壓(hPa)": "SeaLevelPressure",
    "氣溫(℃)": "AirTemperature",
    "露點溫度(℃)": "DewPointTemperature",
    "相對溼度(%)": "RelativeHumidity",
    "風速(m/s) / 風向(360degree)": "WindSpeed,WindDirection",
    "最大瞬間風(m/s) / 最大瞬間風風向(360degree)": "PeakGust",
    "降水量(mm)": "Precipitation",
    "降水時數(hour)": "PrecipitationDuration",
    "日照時數(hour)": "SunshineDuration",
    "全天空日射量(MJ/㎡)": "GlobalSolarRadiation",
    "能見度(km)": "Visibility",
    "能見度_自動(km)": "VisibilityAuto",
    "紫外線指數": "UVIndex",
    "總雲量(0~10)": "TotalCloudAmount",
    "總雲量_衛星(0~10)": "TotalCloudAmountSat",
    "地溫0cm": "SoilTemperatureAt0cm",
    "地溫5cm": "SoilTemperatureAt5cm",
    "地溫10cm": "SoilTemperatureAt10cm",
    "地溫20cm": "SoilTemperatureAt20cm",
    "地溫30cm": "SoilTemperatureAt30cm",
    "地溫50cm": "SoilTemperatureAt50cm",
    "地溫100cm": "SoilTemperatureAt100cm",
}

# one_month：單項逐日年報表
ONE_MONTH_ITEMS: Dict[str, str] = {
    "測站氣壓(hPa)": "StationPressure",
    "海平面氣壓(hPa)": "SeaLevelPressure",
    "測站最高氣壓(hPa) / 測站最高氣壓時間(LST)": "MaxStationPressure",
    "測站最低氣壓(hPa) / 測站最低氣壓時間(LST)": "MinStationPressure",
    "氣溫(℃)": "AirTemperature",
    "最高氣溫(℃) / 最高氣溫時間(LST)": "MaxAirTemperature",
    "最低氣溫(℃) / 最低氣溫時間(LST)": "MinAirTemperature",
    "露點溫度(℃)": "DewPointTemperature",
    "相對溼度(%)": "RelativeHumidity",
    "最小相對溼度(%) / 最小相對溼度時間(LST)": "MinRelativeHumidity",
    "風速(m/s) / 風向(360degree)": "WindSpeed,WindDirection",
    "最大瞬間風(m/s) / 最大瞬間風風向(360degree) / 最大瞬間風風速時間(LST)": "PeakGust",
    "降水量(mm)": "Precipitation",
    "降水時數(hour)": "PrecipitationDuration",
    "最大十分鐘降水量(mm) / 最大十分鐘降雨起始時間(LST)": "MaxTenPrecipitation",
    "最大六十分鐘降水量(mm) / 最大六十分鐘降雨起始時間(LST)": "MaxSixtyPrecipitation",
    "日照時數(hour)": "SunshineDuration",
    "日照率(%)": "SunshineDurationRate",
    "全天空日射量(MJ/㎡)": "GlobalSolarRadiation",
    "能見度(km)": "Visibility",
    "能見度_自動(km)": "VisibilityAuto",
    "A型蒸發量(mm)": "EvaporationClassAPan",
    "日最高紫外線指數 / 日最高紫外線指數時間(LST)": "MaxUVIndex",
    "總雲量(0~10)": "TotalCloudAmount",
    "總雲量_衛星(0~10)": "TotalCloudAmountSat",
    "地溫0cm": "SoilTemperatureAt0cm",
    "地溫5cm": "SoilTemperatureAt5cm",
    "地溫10cm": "SoilTemperatureAt10cm",
    "地溫20cm": "SoilTemperatureAt20cm",
    "地溫30cm": "SoilTemperatureAt30cm",
    "地溫50cm": "SoilTemperatureAt50cm",
    "地溫100cm": "SoilTemperatureAt100cm",
}

# one_year：單項逐月年報表
ONE_YEAR_ITEMS: Dict[str, str] = {
    "測站氣壓(hPa)": "StationPressure",
    "海平面氣壓(hPa)": "SeaLevelPressure",
    "測站最高氣壓(hPa) / 測站最高氣壓時間(LST)": "MaxStationPressure",
    "測站最低氣壓(hPa) / 測站最低氣壓時間(LST)": "MinStationPressure",
    "氣溫(℃)": "AirTemperature",
    "最高氣溫(℃) / 最高氣溫時間(LST)": "MaxAirTemperature",
    "最低氣溫(℃) / 最低氣溫時間(LST)": "MinAirTemperature",
    "露點溫度(℃)": "DewPointTemperature",
    "風速(m/s) / 風向(360degree)": "WindSpeed,WindDirection",
    "最大瞬間風(m/s) / 最大瞬間風風向(360degree) / 最大瞬間風風速時間(LST)": "PeakGust",
    "降水量(mm)": "Precipitation",
    "降水時數(hour)": "PrecipitationDuration",
    "降水日數(day)": "PrecipitationDays",
    "最大十分鐘降水量(mm) / 最大十分鐘降雨起始時間(LST)": "MaxTenPrecipitation",
    "最大六十分鐘降水量(mm) / 最大六十分鐘降雨起始時間(LST)": "MaxSixtyPrecipitation",
    "最大日降雨量(mm)/最大日降雨量時間(LST)": "MaxDailyPrecipitation",
    "相對溼度(%)": "RelativeHumidity",
    "A型蒸發量(mm)": "EvaporationClassAPan",
    "日照時數(hour)": "SunshineDuration",
    "全天空日射量(MJ/㎡)": "GlobalSolarRadiation",
    "平均日最高紫外線指數": "MaxMeanUVIndex",
    "日最高紫外線指數 / 日最高紫外線指數時間(LST)": "MaxUVIndex",
    "總雲量(0~10)": "TotalCloudAmount",
    "總雲量_衛星(0~10)": "TotalCloudAmountSat",
    "地溫0cm": "SoilTemperatureAt0cm",
    "地溫5cm": "SoilTemperatureAt5cm",
    "地溫10cm": "SoilTemperatureAt10cm",
    "地溫20cm": "SoilTemperatureAt20cm",
    "地溫30cm": "SoilTemperatureAt30cm",
    "地溫50cm": "SoilTemperatureAt50cm",
    "地溫100cm": "SoilTemperatureAt100cm",
}

_API_ITEM_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9,]*$")


def _format_item_choices(matches: List[Tuple[str, str]]) -> str:
    """將匹配到的 key／value 編成編號清單。"""
    return "；".join(
        f"{i}. {key} → {value}" for i, (key, value) in enumerate(matches, start=1)
    )


def resolve_item(
    item: str,
    match_index: Optional[int] = None,
    mapping: Optional[Dict[str, str]] = None,
) -> Tuple[bool, Optional[str], str]:
    """將使用者輸入解析為 CODIS API 的 ``item`` 值。

    解析順序：
    1. 與 mapping value 完全相符（不分大小寫）→ 直接使用該 value。
    2. 與 mapping key 完全相符 → 使用對應 value。
    3. 將 ``item`` 視為正則，模糊比對 mapping key。
    4. 若仍無匹配且 ``item`` 本身為 API 代碼格式，直接當作 value。

    多個 key 匹配時，以 ``match_index`` 選擇第幾個（1-based）；
    未填寫或 ``None`` 時使用第 1 個。

    Args:
        item: 中文觀測要素名稱、正則，或英文 API 代碼。
        match_index: 多個 key 匹配時選用的序號，從 1 起算。預設 1。
        mapping: 要搜尋的對照表。預設 ``ONE_DATE_ITEMS``。

    Returns:
        Tuple[bool, Optional[str], str]: 成功與否、解析後的 API item、說明訊息。
    """
    if mapping is None:
        mapping = ONE_DATE_ITEMS

    raw = item.strip() if item is not None else ""
    if not raw:
        return False, None, "請提供觀測要素 item"

    index = 1 if match_index is None else match_index
    if not isinstance(index, int) or isinstance(index, bool) or index < 1:
        return False, None, "match_index 須為大於等於 1 的整數"

    value_lookup = {value.lower(): value for value in mapping.values()}
    if raw.lower() in value_lookup:
        resolved = value_lookup[raw.lower()]
        return True, resolved, f"使用觀測要素 {resolved}"

    if raw in mapping:
        resolved = mapping[raw]
        return True, resolved, f"使用觀測要素「{raw}」→ {resolved}"

    try:
        pattern = re.compile(raw, re.IGNORECASE)
    except re.error as exc:
        return False, None, f"正則表達式無效: {exc}"

    matches = [(key, value) for key, value in mapping.items() if pattern.search(key)]
    if matches:
        if index > len(matches):
            listed = _format_item_choices(matches)
            return (
                False,
                None,
                f"match_index={index} 超出範圍（共 {len(matches)} 個匹配）：{listed}",
            )
        key, value = matches[index - 1]
        suffix = ""
        if len(matches) > 1:
            suffix = f"（第 {index}/{len(matches)} 個匹配）"
        return True, value, f"使用觀測要素「{key}」→ {value}{suffix}"

    if _API_ITEM_PATTERN.fullmatch(raw):
        return True, raw, f"使用觀測要素 {raw}"

    available = "、".join(mapping.keys())
    return False, None, f"找不到符合的觀測要素「{raw}」。可用項目：{available}"


def _unwrap_station_payload(response_data: Any) -> Optional[Dict[str, Any]]:
    """取出含 ``data`` 的區塊；單項報表可能包在 hour／day／month／year 底下。"""
    if not isinstance(response_data, dict):
        return None
    if isinstance(response_data.get("data"), list):
        return response_data
    for wrap_key in ("hour", "day", "month", "year", "date"):
        nested = response_data.get(wrap_key)
        if isinstance(nested, dict) and isinstance(nested.get("data"), list):
            return nested
    return None


def _fetch_single_item(payload: Dict[str, str]) -> Tuple[bool, Optional[CodisData], str]:
    """發送單項報表請求並解析 ``dts``。"""
    try:
        cookie_value = get_valid_cookie()
    except Exception as exc:
        return False, None, f"取得 Cookie 失敗: {exc}"

    current_headers = HEADERS.copy()
    current_headers["Cookie"] = cookie_value

    try:
        response = requests.post(API_URL, headers=current_headers, data=payload)
        response.raise_for_status()
        response_data = response.json()

        unwrapped = _unwrap_station_payload(response_data)
        if (
            unwrapped is not None
            and unwrapped["data"]
            and isinstance(unwrapped["data"][0], dict)
            and "dts" in unwrapped["data"][0]
        ):
            data = unwrapped["data"][0]["dts"]
            if not data:
                return False, None, "下載成功，但內容為空"
            return True, data, "下載成功"

        return False, None, "API 回傳格式不符預期"

    except requests.exceptions.HTTPError as http_err:
        return False, None, f"發生 HTTP 錯誤: {http_err}"
    except json.JSONDecodeError:
        return False, None, "伺服器回應格式錯誤，可能是 Cookie 無效或已被阻擋"
    except requests.exceptions.RequestException as req_err:
        return False, None, f"發生網路錯誤: {req_err}"


def _parse_year(year: int | str) -> int:
    """解析年份。支援 YYYY、YYYYMM、YYYY-MM、YYYY-MM-DD。"""
    text = str(year).strip()
    if text.isdigit() and len(text) == 4:
        value = int(text)
        if value < 1:
            raise ValueError("年份格式錯誤，請使用 YYYY、YYYYMM、YYYY-MM 或 YYYY-MM-DD")
        return value
    try:
        parsed_year, _month = _parse_year_month(text)
        return parsed_year
    except ValueError:
        raise ValueError("年份格式錯誤，請使用 YYYY、YYYYMM、YYYY-MM 或 YYYY-MM-DD")


def _item_filename_slug(item_value: str) -> str:
    """將 API item 轉成檔名可用字串。"""
    return item_value.replace(",", "_")


def _finish_single_item(
    payload: Dict[str, str],
    resolve_message: str,
    return_data: Optional[str],
    output_filename: str,
) -> Tuple[bool, Optional[CodisData], str]:
    """發送請求；成功時可選寫出 JSON，一律回傳 Python 物件。"""
    success, data, message = _fetch_single_item(payload)
    if success:
        message = f"{message}；{resolve_message}"

    output_dir = return_data.strip() if isinstance(return_data, str) else ""
    if success and data is not None and output_dir:
        _save_json(data, os.path.join(output_dir, output_filename))

    return success, data, message


def codis_single_hourly_monthly(
    station_id: str,
    setYM: str,
    item: str,
    match_index: Optional[int] = None,
    return_data: Optional[str] = None,
) -> Tuple[bool, Optional[CodisData], str]:
    """下載指定測站、年月的單項逐時月報表。

    一律回傳 Python 物件 ``(success, data, message)``。
    ``return_data`` 有填路徑時，另外把 JSON 寫到該目錄；未填則不寫檔。

    Args:
        station_id: 測站代碼。
        setYM: 年月，支援 YYYYMM、YYYY-MM 或 YYYY-MM-DD。
        item: 觀測要素。可為對照表中文 key（正則模糊比對）、英文 value，
            或直接傳入 API 代碼。
        match_index: 多個 key 匹配時選用第幾個（1-based）。預設 ``None`` 表示第 1 個。
        return_data: JSON 輸出目錄。未填或空字串時不寫檔，只回傳資料。
    """
    resolved_ok, item_value, resolve_message = resolve_item(
        item, match_index, ONE_DATE_ITEMS
    )
    if not resolved_ok or item_value is None:
        return False, None, resolve_message

    try:
        year, month = _parse_year_month(setYM)
    except ValueError as exc:
        return False, None, str(exc)

    stn_type = _get_stn_type(str(station_id))
    _, last_day = calendar.monthrange(year, month)

    start_date = f"{year:04d}-{month:02d}-01T00:00:00"
    end_date = f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59"

    payload = {
        "date": f"{start_date}+08:00",
        "type": "one_date",
        "stn_ID": str(station_id),
        "stn_type": stn_type,
        "more": "",
        "start": start_date,
        "end": end_date,
        "item": item_value,
    }
    output_filename = (
        f"{year:04d}{month:02d}_{station_id}_{_item_filename_slug(item_value)}.json"
    )
    return _finish_single_item(payload, resolve_message, return_data, output_filename)


def codis_single_daily_yearly(
    station_id: str,
    year: int | str,
    item: str,
    match_index: Optional[int] = None,
    return_data: Optional[str] = None,
) -> Tuple[bool, Optional[CodisData], str]:
    """下載指定測站、年份的單項逐日年報表。

    一律回傳 Python 物件 ``(success, data, message)``。
    ``return_data`` 有填路徑時，另外把 JSON 寫到該目錄；未填則不寫檔。

    Args:
        station_id: 測站代碼。
        year: 年份，支援 YYYY、YYYYMM、YYYY-MM 或 YYYY-MM-DD（後者取其年）。
        item: 觀測要素。可為對照表中文 key（正則模糊比對）、英文 value，
            或直接傳入 API 代碼。
        match_index: 多個 key 匹配時選用第幾個（1-based）。預設 ``None`` 表示第 1 個。
        return_data: JSON 輸出目錄。未填或空字串時不寫檔，只回傳資料。
    """
    resolved_ok, item_value, resolve_message = resolve_item(
        item, match_index, ONE_MONTH_ITEMS
    )
    if not resolved_ok or item_value is None:
        return False, None, resolve_message

    try:
        year_int = _parse_year(year)
    except ValueError as exc:
        return False, None, str(exc)

    stn_type = _get_stn_type(str(station_id))
    start_date = f"{year_int:04d}-01-01T00:00:00"
    end_date = f"{year_int:04d}-12-31T00:00:00"

    payload = {
        "date": f"{start_date}+08:00",
        "type": "one_month",
        "stn_ID": str(station_id),
        "stn_type": stn_type,
        "more": "",
        "start": start_date,
        "end": end_date,
        "item": item_value,
    }
    output_filename = (
        f"{year_int:04d}_{station_id}_{_item_filename_slug(item_value)}.json"
    )
    return _finish_single_item(payload, resolve_message, return_data, output_filename)


def codis_single_monthly_yearly(
    station_id: str,
    year: int | str,
    item: str,
    match_index: Optional[int] = None,
    return_data: Optional[str] = None,
) -> Tuple[bool, Optional[CodisData], str]:
    """下載指定測站、年份的單項逐月年報表。

    一律回傳 Python 物件 ``(success, data, message)``。
    ``return_data`` 有填路徑時，另外把 JSON 寫到該目錄；未填則不寫檔。

    Args:
        station_id: 測站代碼。
        year: 年份，支援 YYYY、YYYYMM、YYYY-MM 或 YYYY-MM-DD（後者取其年）。
        item: 觀測要素。可為對照表中文 key（正則模糊比對）、英文 value，
            或直接傳入 API 代碼。
        match_index: 多個 key 匹配時選用第幾個（1-based）。預設 ``None`` 表示第 1 個。
        return_data: JSON 輸出目錄。未填或空字串時不寫檔，只回傳資料。
    """
    resolved_ok, item_value, resolve_message = resolve_item(
        item, match_index, ONE_YEAR_ITEMS
    )
    if not resolved_ok or item_value is None:
        return False, None, resolve_message

    try:
        year_int = _parse_year(year)
    except ValueError as exc:
        return False, None, str(exc)

    stn_type = _get_stn_type(str(station_id))
    start_date = f"{year_int:04d}-01-01T00:00:00"
    end_date = f"{year_int:04d}-12-31T00:00:00"

    payload = {
        "date": f"{start_date}+08:00",
        "type": "one_year",
        "stn_ID": str(station_id),
        "stn_type": stn_type,
        "more": "",
        "start": start_date,
        "end": end_date,
        "item": item_value,
    }
    output_filename = (
        f"{year_int:04d}_{station_id}_{_item_filename_slug(item_value)}_monthly.json"
    )
    return _finish_single_item(payload, resolve_message, return_data, output_filename)
