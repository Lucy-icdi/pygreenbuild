"""中央氣象署 OpenData 鄉鎮天氣預報擷取（未來 3 天／未來 1 週）。

資料來源為 CWA OpenData 的逐縣市鄉鎮天氣預報資料集（`F-D0047-XXX`），
需要 API 授權碼，由 `api_key` 參數傳入。

未指定縣市時批次下載全部 22 個縣市；也可用縣市名稱（例：`"臺北市"`）或
資料編號（例：`"F-D0047-083"`）指定只下載該縣市。

回傳與寫檔慣例與 `codis_crawler_tojson` 一致：
- `return_data=False` → `(success, message)`
- `return_data=True` → `(success, data, message)`
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union, overload

import requests

# --- 共用常數與設定 ---
API_BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"

REQUEST_TIMEOUT = 30

HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'pygreenbuild/weather_crawler',
}

# 縣市名稱 → (未來 3 天資料編號, 未來 1 週資料編號)
COUNTY_DATASET_IDS: Dict[str, Tuple[str, str]] = {
    "宜蘭縣": ("F-D0047-001", "F-D0047-003"),
    "桃園市": ("F-D0047-005", "F-D0047-007"),
    "新竹縣": ("F-D0047-009", "F-D0047-011"),
    "苗栗縣": ("F-D0047-013", "F-D0047-015"),
    "彰化縣": ("F-D0047-017", "F-D0047-019"),
    "南投縣": ("F-D0047-021", "F-D0047-023"),
    "雲林縣": ("F-D0047-025", "F-D0047-027"),
    "嘉義縣": ("F-D0047-029", "F-D0047-031"),
    "屏東縣": ("F-D0047-033", "F-D0047-035"),
    "臺東縣": ("F-D0047-037", "F-D0047-039"),
    "花蓮縣": ("F-D0047-041", "F-D0047-043"),
    "澎湖縣": ("F-D0047-045", "F-D0047-047"),
    "基隆市": ("F-D0047-049", "F-D0047-051"),
    "新竹市": ("F-D0047-053", "F-D0047-055"),
    "嘉義市": ("F-D0047-057", "F-D0047-059"),
    "臺北市": ("F-D0047-061", "F-D0047-063"),
    "高雄市": ("F-D0047-065", "F-D0047-067"),
    "新北市": ("F-D0047-069", "F-D0047-071"),
    "臺中市": ("F-D0047-073", "F-D0047-075"),
    "臺南市": ("F-D0047-077", "F-D0047-079"),
    "連江縣": ("F-D0047-081", "F-D0047-083"),
    "金門縣": ("F-D0047-085", "F-D0047-087"),
}

INDEX_3DAY = 0
INDEX_WEEK = 1

_DATASET_ID_TO_COUNTY: Dict[str, str] = {
    dataset_id: county
    for county, dataset_ids in COUNTY_DATASET_IDS.items()
    for dataset_id in dataset_ids
}

ForecastData = List[Dict[str, Any]]


# --- 共用輔助函式 ---
def _resolve_county(target: str) -> Tuple[Optional[str], str]:
    """將縣市名稱或資料編號解析為標準縣市名稱。

    Args:
        target: 縣市名稱（例：`"臺北市"`、`"台北市"`）或資料編號
            （例：`"F-D0047-083"`、`"F_D0047_083"`）。

    Returns:
        Tuple[Optional[str], str]: 縣市名稱（無法解析時為 None）、錯誤訊息。
    """
    text = str(target).strip()
    if not text:
        return None, "縣市別或資料編號不可為空白"

    dataset_id = text.upper().replace("_", "-")
    if dataset_id in _DATASET_ID_TO_COUNTY:
        return _DATASET_ID_TO_COUNTY[dataset_id], ""

    county = text.replace("台", "臺")
    if county in COUNTY_DATASET_IDS:
        return county, ""

    return None, f"無法識別的縣市別或資料編號：{text}"


def _resolve_counties(
    targets: Tuple[str, ...]
) -> Tuple[Optional[List[str]], str]:
    """未指定時回傳全部 22 個縣市，否則逐一解析並去除重複。"""
    if not targets:
        return list(COUNTY_DATASET_IDS), ""

    counties: List[str] = []
    for target in targets:
        county, error = _resolve_county(target)
        if county is None:
            return None, error
        if county not in counties:
            counties.append(county)

    return counties, ""


def _fetch_forecast(
    dataset_id: str,
    api_key: str,
) -> Tuple[bool, Optional[ForecastData], str]:
    """下載單一資料集並解析 OpenData 回應。

    Args:
        dataset_id: CWA 資料編號（例：`"F-D0047-001"`）。
        api_key: CWA OpenData 授權碼。

    Returns:
        Tuple[bool, Optional[ForecastData], str]: 成功與否、`records.Locations`
            內容（失敗時為 None）、訊息。
    """
    params: Dict[str, Any] = {'Authorization': api_key, 'format': 'JSON'}
    url = f"{API_BASE_URL}/{dataset_id}"

    try:
        response = requests.get(
            url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        response_data = response.json()

        if not isinstance(response_data, dict):
            return False, None, "API 回傳格式不符預期"

        if str(response_data.get('success', '')).lower() not in ('true', '1'):
            return False, None, "API 回報失敗，請確認授權碼與資料編號"

        records = response_data.get('records')
        if not isinstance(records, dict):
            return False, None, "API 回傳格式不符預期"

        locations = records.get('Locations')
        if not isinstance(locations, list):
            return False, None, "API 回傳格式不符預期"

        if not locations or not any(loc.get('Location') for loc in locations):
            return False, None, "下載成功，但內容為空"

        return True, locations, "下載成功"

    except requests.exceptions.HTTPError as http_err:
        status = getattr(http_err.response, 'status_code', None)
        if status == 401:
            return False, None, "授權失敗（401），請確認 CWA API 授權碼"
        return False, None, f"發生 HTTP 錯誤: {http_err}"
    except json.JSONDecodeError:
        return False, None, "伺服器回應格式錯誤，無法解析 JSON"
    except requests.exceptions.RequestException as req_err:
        return False, None, f"發生網路錯誤: {req_err}"


def _save_json(data: ForecastData, output_path: str) -> None:
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def _build_output_path(output_dir: str, suffix: str, county: str) -> str:
    """組出 `{今日日期}_township_{suffix}_{縣市}.json` 的輸出路徑。"""
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(output_dir, f"{today}_township_{suffix}_{county}.json")


def _download_forecast(
    dataset_index: int,
    suffix: str,
    api_key: str,
    output_dir: Optional[str],
    targets: Tuple[str, ...],
    *,
    return_data: bool,
) -> Union[Tuple[bool, str], Tuple[bool, Optional[ForecastData], str]]:
    def fail(message: str):
        if return_data:
            return False, None, message
        return False, message

    if not return_data and not output_dir:
        return fail("匯出 JSON 模式需提供 output_dir")

    resolved_key = str(api_key).strip() if api_key else ""
    if not resolved_key:
        return fail("缺少 CWA API 授權碼，請以 api_key 傳入")

    counties, error = _resolve_counties(targets)
    if counties is None:
        return fail(error)

    collected: ForecastData = []
    failures: List[str] = []

    for county in counties:
        dataset_id = COUNTY_DATASET_IDS[county][dataset_index]
        success, data, message = _fetch_forecast(dataset_id, resolved_key)

        if not success or data is None:
            failures.append(f"{county}（{dataset_id}）：{message}")
            continue

        if output_dir:
            _save_json(data, _build_output_path(output_dir, suffix, county))
        collected.extend(data)

    total = len(counties)
    if failures:
        message = (
            f"下載完成 {total - len(failures)}/{total} 個縣市；"
            f"失敗：{'、'.join(failures)}"
        )
    else:
        message = f"下載成功：{total} 個縣市"

    success = not failures
    if return_data:
        return success, (collected or None), message
    return success, message


# --- 主要功能函式 ---

@overload
def cwa_township_forecast_3day(
    api_key: str,
    output_dir: Optional[str],
    *counties: str,
    return_data: bool = False,
) -> Tuple[bool, str]: ...


@overload
def cwa_township_forecast_3day(
    api_key: str,
    output_dir: Optional[str],
    *counties: str,
    return_data: bool = True,
) -> Tuple[bool, Optional[ForecastData], str]: ...


def cwa_township_forecast_3day(
    api_key: str,
    output_dir: Optional[str],
    *counties: str,
    return_data: bool = False,
) -> Union[Tuple[bool, str], Tuple[bool, Optional[ForecastData], str]]:
    """下載鄉鎮天氣預報－未來 3 天（逐 3 小時）。

    Args:
        api_key: CWA OpenData 授權碼（例：`"CWA-F8F425DD-****"`）。
        output_dir: JSON 輸出目錄；`return_data=False` 時必填。每個縣市寫出一個檔案。
        *counties: 縣市名稱（例：`"臺北市"`）或資料編號（例：`"F-D0047-061"`）；
            不指定則批次下載全部 22 個縣市。資料編號只用來辨識縣市，實際下載的
            仍是該縣市的未來 3 天資料集。
        return_data: 為 True 時一併回傳資料供後續處理。

    Returns:
        `return_data=False` 時為 `(success, message)`；`return_data=True` 時為
        `(success, data, message)`。只要有任一縣市失敗，`success` 即為 False，
        失敗的縣市會列於 `message`；`data` 僅在完全沒取得資料時為 None。
    """
    return _download_forecast(
        INDEX_3DAY,
        "3day",
        api_key,
        output_dir,
        counties,
        return_data=return_data,
    )


@overload
def cwa_township_forecast_week(
    api_key: str,
    output_dir: Optional[str],
    *counties: str,
    return_data: bool = False,
) -> Tuple[bool, str]: ...


@overload
def cwa_township_forecast_week(
    api_key: str,
    output_dir: Optional[str],
    *counties: str,
    return_data: bool = True,
) -> Tuple[bool, Optional[ForecastData], str]: ...


def cwa_township_forecast_week(
    api_key: str,
    output_dir: Optional[str],
    *counties: str,
    return_data: bool = False,
) -> Union[Tuple[bool, str], Tuple[bool, Optional[ForecastData], str]]:
    """下載鄉鎮天氣預報－未來 1 週（逐 12 小時）。

    Args:
        api_key: CWA OpenData 授權碼（例：`"CWA-F8F425DD-****"`）。
        output_dir: JSON 輸出目錄；`return_data=False` 時必填。每個縣市寫出一個檔案。
        *counties: 縣市名稱（例：`"臺北市"`）或資料編號（例：`"F-D0047-083"`）；
            不指定則批次下載全部 22 個縣市。資料編號只用來辨識縣市，實際下載的
            仍是該縣市的未來 1 週資料集。
        return_data: 為 True 時一併回傳資料供後續處理。

    Returns:
        `return_data=False` 時為 `(success, message)`；`return_data=True` 時為
        `(success, data, message)`。只要有任一縣市失敗，`success` 即為 False，
        失敗的縣市會列於 `message`；`data` 僅在完全沒取得資料時為 None。
    """
    return _download_forecast(
        INDEX_WEEK,
        "week",
        api_key,
        output_dir,
        counties,
        return_data=return_data,
    )
