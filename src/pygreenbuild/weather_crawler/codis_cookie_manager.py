# cookie_manager.py
import requests
import time
from typing import Optional

# Cookie 快取機制
_cookie_cache = None
_last_cookie_update = 0
COOKIE_VALIDITY = 21600  # Cookie 有效期限為6小時

def get_codis_cookie() -> Optional[str]:
    """
    從 CODis 網站取得最新的 Cookie
    """
    try:
        # 造訪首頁取得 Cookie
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }
        
        # 造訪首頁取得初始 Cookie
        response = session.get('https://codis.cwa.gov.tw/StationData', 
                             headers=headers, timeout=30)
        response.raise_for_status()
        
        # 取得 Cookie
        cookie_dict = session.cookies.get_dict()
        cookie_parts = [f"{key}={value}" for key, value in cookie_dict.items()]
        cookie_str = '; '.join(cookie_parts)
        
        print(f"✅ 成功取得 Cookie")
        return cookie_str
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 取得 Cookie 失敗: {e}")
        return None
    except Exception as e:
        print(f"❌ 取得 Cookie 時發生未知錯誤: {e}")
        return None

def validate_cookie(cookie: str) -> bool:
    """
    驗證 Cookie 是否有效
    """
    try:
        headers = {
            'Cookie': cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }
        
        # 發送一個簡單的測試請求
        test_url = "https://codis.cwa.gov.tw/api/station"
        test_payload = {
            'date': '2024-01-01T00:00:00.000+08:00',
            'type': 'report_month',
            'stn_ID': '466920',
            'stn_type': 'cwb',
            'more': '',
            'start': '2024-01-01T00:00:00',
            'end': '2024-01-31T00:00:00',
            'item': ''
        }
        
        response = requests.post(test_url, headers=headers, data=test_payload, timeout=10)
        return response.status_code == 200
        
    except:
        return False

def get_valid_cookie() -> str:
    """
    取得有效的 Cookie，使用快取機制避免頻繁請求
    """
    global _cookie_cache, _last_cookie_update
    
    current_time = time.time()
    
    # 如果緩存存在且未過期，直接返回
    if (_cookie_cache and 
        (current_time - _last_cookie_update) < COOKIE_VALIDITY and
        validate_cookie(_cookie_cache)):
        return _cookie_cache
    
    # 否則取得新的 Cookie
    max_retries = 3
    for attempt in range(max_retries):
        new_cookie = get_codis_cookie()
        if new_cookie and validate_cookie(new_cookie):
            _cookie_cache = new_cookie
            _last_cookie_update = current_time
            return new_cookie
        
        print(f"⚠️ 第 {attempt + 1} 次取得 Cookie 失敗，重試中...")
        time.sleep(2)
    
    # 如果所有重試都失敗，拋出異常
    raise Exception("無法取得有效的 Cookie，請檢查網路連線或網站狀態")