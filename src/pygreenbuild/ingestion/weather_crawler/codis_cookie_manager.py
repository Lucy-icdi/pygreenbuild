"""CODIS Session Cookie 取得、驗證與快取。"""

from __future__ import annotations

import ssl
import time
from typing import Optional

import requests
from requests.adapters import HTTPAdapter

# Cookie 快取機制
_cookie_cache: Optional[str] = None
_last_cookie_update: float = 0
COOKIE_VALIDITY = 21600  # Cookie 有效期限為 6 小時

STATION_PAGE_URL = "https://codis.cwa.gov.tw/StationData"
STATION_API_URL = "https://codis.cwa.gov.tw/api/station"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/139.0.0.0 Safari/537.36"
)


def _build_cwa_ssl_context() -> ssl.SSLContext:
    """建立仍驗證憑證、但略過 Python 3.13+ 過嚴 X.509 檢查的 SSL 上下文。

    中央氣象署（CWA）網站憑證鏈接到 TWCA。Python 3.13 起
    ``ssl.create_default_context()`` 預設啟用 ``VERIFY_X509_STRICT``，
    會因憑證缺少 Subject Key Identifier 而握手失敗。此處只關閉該旗標，
    仍保留憑證簽章、主機名稱與有效期限驗證。

    Returns:
        ssl.SSLContext: 可用於 CODIS HTTPS 連線的 SSL 上下文。
    """
    context = ssl.create_default_context()
    strict_flag = getattr(ssl, "VERIFY_X509_STRICT", 0)
    if strict_flag:
        context.verify_flags &= ~strict_flag
    return context


class _CwaSSLAdapter(HTTPAdapter):
    """對 CODIS HTTPS 連線套用相容 Python 3.12–3.14 的 SSL 上下文。"""

    def init_poolmanager(
        self,
        connections: int,
        maxsize: int,
        block: bool = False,
        **pool_kwargs: object,
    ) -> None:
        """初始化連線池，注入略過 ``VERIFY_X509_STRICT`` 的 SSL 上下文。"""
        pool_kwargs["ssl_context"] = _build_cwa_ssl_context()
        super().init_poolmanager(connections, maxsize, block, **pool_kwargs)

    def proxy_manager_for(self, proxy: str, **proxy_kwargs: object) -> object:
        """建立 proxy manager 時同樣注入相容的 SSL 上下文。"""
        proxy_kwargs["ssl_context"] = _build_cwa_ssl_context()
        return super().proxy_manager_for(proxy, **proxy_kwargs)


def _codis_session() -> requests.Session:
    """建立已掛上 CWA 相容 SSL adapter 的 ``requests.Session``。

    Returns:
        requests.Session: 用於造訪 CODIS 的工作階段。
    """
    session = requests.Session()
    adapter = _CwaSSLAdapter()
    session.mount("https://", adapter)
    return session


def get_codis_cookie() -> Optional[str]:
    """從 CODIS 網站取得最新的 Cookie。

    Returns:
        Optional[str]: Cookie 標頭字串（例：``PHPSESSID=...``）；失敗時為 ``None``。
    """
    try:
        headers = {"User-Agent": USER_AGENT}

        with _codis_session() as session:
            response = session.get(STATION_PAGE_URL, headers=headers, timeout=30)
            response.raise_for_status()

            cookie_parts = [
                f"{cookie.name}={cookie.value}"
                for cookie in session.cookies
                if cookie.value is not None
            ]
            cookie_str = "; ".join(cookie_parts)

        if not cookie_str:
            print("❌ 取得 Cookie 失敗: 回應未包含可用 Cookie")
            return None

        print("✅ 成功取得 Cookie")
        return cookie_str

    except requests.exceptions.RequestException as e:
        print(f"❌ 取得 Cookie 失敗: {e}")
        return None
    except Exception as e:
        print(f"❌ 取得 Cookie 時發生未知錯誤: {e}")
        return None


def validate_cookie(cookie: str) -> bool:
    """驗證 Cookie 是否有效。

    Args:
        cookie: 要驗證的 Cookie 標頭字串。單位：不適用。

    Returns:
        bool: HTTP 狀態碼為 200 時為 ``True``，否則為 ``False``。
    """
    try:
        headers = {
            "Cookie": cookie,
            "User-Agent": USER_AGENT,
        }

        test_payload = {
            "date": "2024-01-01T00:00:00.000+08:00",
            "type": "report_month",
            "stn_ID": "466920",
            "stn_type": "cwb",
            "more": "",
            "start": "2024-01-01T00:00:00",
            "end": "2024-01-31T00:00:00",
            "item": "",
        }

        with _codis_session() as session:
            response = session.post(
                STATION_API_URL, headers=headers, data=test_payload, timeout=10
            )
        return response.status_code == 200

    except Exception:
        return False


def get_valid_cookie() -> str:
    """取得有效的 Cookie，使用快取機制避免頻繁請求。

    Returns:
        str: 通過驗證的 Cookie 標頭字串。

    Raises:
        Exception: 重試後仍無法取得有效 Cookie。
    """
    global _cookie_cache, _last_cookie_update

    current_time = time.time()

    if (
        _cookie_cache
        and (current_time - _last_cookie_update) < COOKIE_VALIDITY
        and validate_cookie(_cookie_cache)
    ):
        return _cookie_cache

    max_retries = 3
    for attempt in range(max_retries):
        new_cookie = get_codis_cookie()
        if new_cookie and validate_cookie(new_cookie):
            _cookie_cache = new_cookie
            _last_cookie_update = current_time
            return new_cookie

        print(f"⚠️ 第 {attempt + 1} 次取得 Cookie 失敗，重試中...")
        time.sleep(2)

    raise Exception("無法取得有效的 Cookie，請檢查網路連線或網站狀態")
