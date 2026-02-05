import requests
import json
import os
import calendar
from typing import Tuple, Dict ,Optional
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

def _fetch_and_save_data(payload: Dict, output_path: str) -> Tuple[bool, str]:
    """
    核心函式，負責發送請求、處理回應和儲存資料。

    Args:
        payload (Dict): 請求的負載資料。
        output_path (str): 輸出的完整檔案路徑。

    Returns:
        Tuple[bool, str]: 回傳操作是否成功及對應的訊息。
    """
    try:
        cookie_value = get_valid_cookie()
    except Exception as e:
        reason = f"取得 Cookie 失敗: {e}"
        return False, reason
    
    current_headers = HEADERS.copy()
    current_headers['Cookie'] = cookie_value
    
    try:
        response = requests.post(API_URL, headers=current_headers, data=payload)
        response.raise_for_status()
        response_data = response.json()

        if (isinstance(response_data, dict) and 'data' in response_data and 
            isinstance(response_data['data'], list) and len(response_data['data']) > 0 and
            'dts' in response_data['data'][0]):
            
            data_to_save = response_data['data'][0]['dts']
            
            if not data_to_save:
                return False, "下載成功，但內容為空"

            # 確保輸出目錄存在
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)

            return True, "下載成功"
        else:
            return False, "API 回傳格式不符預期"

    except requests.exceptions.HTTPError as http_err:
        return False, f"發生 HTTP 錯誤: {http_err}"
    except json.JSONDecodeError:
        return False, "伺服器回應格式錯誤，可能是 Cookie 無效或已被阻擋"
    except requests.exceptions.RequestException as req_err:
        return False, f"發生網路錯誤: {req_err}"

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

def codis_yearly(station_id, output_dir: str, year) -> Tuple[bool, str]:
    """下載指定測站的年度資料"""
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
    
    output_filename = f"{year_str}_{station_id_str}.json"
    output_path = os.path.join(output_dir, output_filename)
    
    return _fetch_and_save_data(payload, output_path)

def codis_monthly(station_id: str, output_dir: str,setYM: str) -> Tuple[bool, str]:
    try:
        year, month = _parse_year_month(setYM)
    except ValueError as e:
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
    
    output_filename = f"{year:04d}{month:02d}_{station_id}.json"
    output_path = os.path.join(output_dir, output_filename)

    return _fetch_and_save_data(payload, output_path)


def codis_daily(
        station_id: str,
        output_dir: str,
        *dates: str
) -> Tuple[bool, str]:
    """
    下載單日或多日氣象資料。
    若輸入多個日期，會自動取最小值與最大值作為區間，間隔不得超過 30 天。
    """

    # 1. 參數檢查
    if not dates:
        return False, "請至少提供一個日期參數 (YYYY-MM-DD)"

    # 2. 轉換日期物件並排序
    try:
        # 將字串轉換為 datetime 物件以便計算
        date_objs = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
        sorted_date_objs = sorted(date_objs)
    except ValueError:
        return False, "日期格式錯誤，請使用 YYYY-MM-DD (例如: 2024-11-01)"

    start_obj = sorted_date_objs[0]
    end_obj = sorted_date_objs[-1]

    # 3. 計算間隔天數並執行嚴格檢查
    delta_days = (end_obj - start_obj).days

    if len(dates) > 1 and delta_days > 31:
        # 直接報錯停止
        return False, f"❌ 下載失敗：日期間隔為 {delta_days} 天，超過系統限制 (31 天)。"

    # 4. 準備字串格式
    start_str = start_obj.strftime("%Y-%m-%d")
    end_str = end_obj.strftime("%Y-%m-%d")
    stn_type = _get_stn_type(station_id)

    if start_str == end_str:
        # 單日模式
        start_date = f"{start_str}T00:00:00"
        end_date = f"{start_str}T23:59:59"
        output_filename = f"{start_str}_{station_id}.json"
    else:
        # 多日模式
        start_date = f"{start_str}T00:00:00"
        end_date = f"{end_str}T23:59:59"
        output_filename = f"{start_str}~{end_str}_{station_id}.json"

    date_for_payload = f"{start_str}.000+08:00"

    # 5. 組裝 Payload
    payload = {
        'date': date_for_payload,
        'type': 'report_date',
        'stn_ID': station_id,
        'stn_type': stn_type,
        'more': '',
        'start': start_date,
        'end': end_date,
        'item': ''
    }

    # 6. 交由 _fetch_and_save_data 處理資料夾檢查與存檔
    output_path = os.path.join(output_dir, output_filename)
    return _fetch_and_save_data(payload, output_path)
