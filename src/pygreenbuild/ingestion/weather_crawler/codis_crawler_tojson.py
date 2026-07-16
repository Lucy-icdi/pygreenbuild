import requests
import json
import os
import calendar
from typing import Tuple, Dict, Optional, List, Any, overload, Union
from datetime import datetime
from .codis_cookie_manager import get_valid_cookie

# --- 共用常數與設定 ---
API_URL = "https://codis.cwa.gov.tw/api/station"
# 共用的請求標頭，Cookie 將在執行時動態加入
HEADERS = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://codis.cwa.gov.tw',
    'Referer': 'https://codis.cwa.gov.tw/StationData',
    'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

CodisData = List[Dict[str, Any]]

# --- 共用輔助函式 ---
def _get_stn_type(station_id: str) -> str:
    """根據測站 ID 返回對應的測站類型"""
    if station_id.startswith('46'):
        return 'cwb'
    elif station_id.startswith('C0'):
        return 'auto_C0'
    elif station_id.startswith('C1'):
        return 'auto_C1'
    else:
        return 'agr'


def _fetch_data(payload: Dict) -> Tuple[bool, Optional[CodisData], str]:
    """
    核心函式，負責發送請求並解析回應資料。

    Returns:
        Tuple[bool, Optional[CodisData], str]: 成功與否、資料（失敗時為 None）、訊息。
    """
    try:
        cookie_value = get_valid_cookie()
    except Exception as e:
        return False, None, f"取得 Cookie 失敗: {e}"

    current_headers = HEADERS.copy()
    current_headers['Cookie'] = cookie_value

    try:
        response = requests.post(API_URL, headers=current_headers, data=payload)
        response.raise_for_status()
        response_data = response.json()

        if (isinstance(response_data, dict) and 'data' in response_data and
            isinstance(response_data['data'], list) and len(response_data['data']) > 0 and
            'dts' in response_data['data'][0]):

            data = response_data['data'][0]['dts']

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


def _save_json(data: CodisData, output_path: str) -> None:
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def _finalize_result(
    success: bool,
    data: Optional[CodisData],
    message: str,
    *,
    return_data: bool,
    output_path: Optional[str] = None,
) -> Union[Tuple[bool, str], Tuple[bool, Optional[CodisData], str]]:
    if success and data is not None and output_path:
        _save_json(data, output_path)

    if return_data:
        return success, data, message
    return success, message


def _parse_year_month(setYM: str) -> tuple[int, int]:
    """
    Internal helper.
    支援：
    - YYYYMM
    - YYYY-MM
    - YYYY-MM-DD
    """
    try:
        if setYM.isdigit() and len(setYM) == 6:
            year = int(setYM[:4])
            month = int(setYM[4:6])
        else:
            fmt = "%Y-%m-%d" if len(setYM) == 10 else "%Y-%m"
            dt = datetime.strptime(setYM, fmt)
            year, month = dt.year, dt.month

        if not (1 <= month <= 12):
            raise ValueError

        return year, month

    except Exception:
        raise ValueError("日期格式錯誤，請使用 YYYYMM、YYYY-MM 或 YYYY-MM-DD")

# --- 主要功能函式 ---

@overload
def codis_yearly(
    station_id,
    output_dir: Optional[str],
    year,
    *,
    return_data: bool = False,
) -> Tuple[bool, str]: ...


@overload
def codis_yearly(
    station_id,
    output_dir: Optional[str],
    year,
    *,
    return_data: bool = True,
) -> Tuple[bool, Optional[CodisData], str]: ...


def codis_yearly(
    station_id,
    output_dir: Optional[str],
    year,
    *,
    return_data: bool = False,
) -> Union[Tuple[bool, str], Tuple[bool, Optional[CodisData], str]]:
    """下載指定測站的年度資料。

    Args:
        station_id: 測站代碼。
        output_dir: JSON 輸出目錄；`return_data=False` 時必填。
        year: 年份。
        return_data: 為 True 時回傳資料供後續處理；為 False 時僅匯出 JSON。
    """
    if not return_data and not output_dir:
        return False, "匯出 JSON 模式需提供 output_dir"

    year_str = str(year)
    station_id_str = str(station_id)
    stn_type = _get_stn_type(station_id_str)
    start_date = f"{year_str}-01-01T00:00:00"
    end_date = f"{year_str}-12-31T00:00:00"

    payload = {
        'date': f'{start_date}.000+08:00',
        'type': 'report_year',
        'stn_ID': station_id_str,
        'stn_type': stn_type,
        'more': '',
        'start': start_date,
        'end': end_date,
        'item': ''
    }

    output_path = None
    if output_dir:
        output_filename = f"{year_str}_{station_id_str}.json"
        output_path = os.path.join(output_dir, output_filename)

    success, data, message = _fetch_data(payload)
    return _finalize_result(
        success, data, message, return_data=return_data, output_path=output_path
    )


@overload
def codis_monthly(
    station_id: str,
    output_dir: Optional[str],
    setYM: str,
    *,
    return_data: bool = False,
) -> Tuple[bool, str]: ...


@overload
def codis_monthly(
    station_id: str,
    output_dir: Optional[str],
    setYM: str,
    *,
    return_data: bool = True,
) -> Tuple[bool, Optional[CodisData], str]: ...


def codis_monthly(
    station_id: str,
    output_dir: Optional[str],
    setYM: str,
    *,
    return_data: bool = False,
) -> Union[Tuple[bool, str], Tuple[bool, Optional[CodisData], str]]:
    """下載指定測站的月份資料。

    Args:
        station_id: 測站代碼。
        output_dir: JSON 輸出目錄；`return_data=False` 時必填。
        setYM: 年月，支援 YYYYMM、YYYY-MM 或 YYYY-MM-DD。
        return_data: 為 True 時回傳資料供後續處理；為 False 時僅匯出 JSON。
    """
    if not return_data and not output_dir:
        return False, "匯出 JSON 模式需提供 output_dir"

    try:
        year, month = _parse_year_month(setYM)
    except ValueError as e:
        if return_data:
            return False, None, str(e)
        return False, str(e)

    stn_type = _get_stn_type(station_id)
    _, last_day = calendar.monthrange(year, month)

    start_date = f"{year:04d}-{month:02d}-01T00:00:00"
    end_date = f"{year:04d}-{month:02d}-{last_day:02d}T00:00:00"

    payload = {
        'date': f'{start_date}.000+08:00',
        'type': 'report_month',
        'stn_ID': station_id,
        'stn_type': stn_type,
        'more': '',
        'start': start_date,
        'end': end_date,
        'item': ''
    }

    output_path = None
    if output_dir:
        output_filename = f"{year:04d}{month:02d}_{station_id}.json"
        output_path = os.path.join(output_dir, output_filename)

    success, data, message = _fetch_data(payload)
    return _finalize_result(
        success, data, message, return_data=return_data, output_path=output_path
    )


@overload
def codis_daily(
    station_id: str,
    output_dir: Optional[str],
    *dates: str,
    return_data: bool = False,
) -> Tuple[bool, str]: ...


@overload
def codis_daily(
    station_id: str,
    output_dir: Optional[str],
    *dates: str,
    return_data: bool = True,
) -> Tuple[bool, Optional[CodisData], str]: ...


def codis_daily(
    station_id: str,
    output_dir: Optional[str],
    *dates: str,
    return_data: bool = False,
) -> Union[Tuple[bool, str], Tuple[bool, Optional[CodisData], str]]:
    """
    下載單日或多日氣象資料。
    若輸入多個日期，會自動取最小值與最大值作為區間，間隔不得超過 31 天。

    Args:
        station_id: 測站代碼。
        output_dir: JSON 輸出目錄；`return_data=False` 時必填。
        *dates: 一個或多個日期 (YYYY-MM-DD)。
        return_data: 為 True 時回傳資料供後續處理；為 False 時僅匯出 JSON。
    """
    if not return_data and not output_dir:
        return False, "匯出 JSON 模式需提供 output_dir"

    if not dates:
        message = "請至少提供一個日期參數 (YYYY-MM-DD)"
        if return_data:
            return False, None, message
        return False, message

    try:
        date_objs = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
        sorted_date_objs = sorted(date_objs)
    except ValueError:
        message = "日期格式錯誤，請使用 YYYY-MM-DD (例如: 2024-11-01)"
        if return_data:
            return False, None, message
        return False, message

    start_obj = sorted_date_objs[0]
    end_obj = sorted_date_objs[-1]
    delta_days = (end_obj - start_obj).days

    if len(dates) > 1 and delta_days > 31:
        message = f"❌ 下載失敗：日期間隔為 {delta_days} 天，超過系統限制 (31 天)。"
        if return_data:
            return False, None, message
        return False, message

    start_str = start_obj.strftime("%Y-%m-%d")
    end_str = end_obj.strftime("%Y-%m-%d")
    stn_type = _get_stn_type(station_id)

    if start_str == end_str:
        start_date = f"{start_str}T00:00:00"
        end_date = f"{start_str}T23:59:59"
        output_filename = f"{start_str}_{station_id}.json"
    else:
        start_date = f"{start_str}T00:00:00"
        end_date = f"{end_str}T23:59:59"
        output_filename = f"{start_str}~{end_str}_{station_id}.json"

    payload = {
        'date': f"{start_str}.000+08:00",
        'type': 'report_date',
        'stn_ID': station_id,
        'stn_type': stn_type,
        'more': '',
        'start': start_date,
        'end': end_date,
        'item': ''
    }

    output_path = None
    if output_dir:
        output_path = os.path.join(output_dir, output_filename)

    success, data, message = _fetch_data(payload)
    return _finalize_result(
        success, data, message, return_data=return_data, output_path=output_path
    )
