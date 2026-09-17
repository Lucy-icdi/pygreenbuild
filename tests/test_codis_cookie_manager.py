"""codis_cookie_manager 單元測試（mock HTTP，不打真實網路）。"""

from __future__ import annotations

import ssl
from unittest.mock import MagicMock, patch

import pytest
import requests

from pygreenbuild.ingestion.weather_crawler import codis_cookie_manager as cookie_mod
from pygreenbuild.ingestion.weather_crawler.codis_cookie_manager import (
    _build_cwa_ssl_context,
    _codis_session,
    _CwaSSLAdapter,
    get_codis_cookie,
    get_valid_cookie,
    validate_cookie,
)

MODULE = "pygreenbuild.ingestion.weather_crawler.codis_cookie_manager"


@pytest.fixture(autouse=True)
def _reset_cookie_cache() -> None:
    cookie_mod._cookie_cache = None
    cookie_mod._last_cookie_update = 0
    yield
    cookie_mod._cookie_cache = None
    cookie_mod._last_cookie_update = 0


def _session_with_cookies(**cookies: str) -> MagicMock:
    session = MagicMock()
    jar = requests.cookies.RequestsCookieJar()
    for name, value in cookies.items():
        jar.set(name, value, domain="codis.cwa.gov.tw", path="/")
    session.cookies = jar
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.status_code = 200
    session.get.return_value = response
    session.post.return_value = response
    session.__enter__.return_value = session
    session.__exit__.return_value = False
    return session


class TestBuildCwaSslContext:
    def test_keeps_certificate_verification(self) -> None:
        context = _build_cwa_ssl_context()

        assert context.verify_mode == ssl.CERT_REQUIRED
        assert context.check_hostname is True

    def test_clears_strict_flag_when_available(self) -> None:
        context = _build_cwa_ssl_context()
        strict_flag = getattr(ssl, "VERIFY_X509_STRICT", 0)

        if strict_flag:
            assert context.verify_flags & strict_flag == 0


class TestCodisSession:
    def test_mounts_https_adapter(self) -> None:
        session = _codis_session()
        adapter = session.get_adapter("https://codis.cwa.gov.tw/StationData")

        assert isinstance(adapter, _CwaSSLAdapter)


class TestGetCodisCookie:
    @patch(f"{MODULE}._codis_session")
    def test_joins_cookies_from_session(self, mock_session_factory: MagicMock) -> None:
        mock_session_factory.return_value = _session_with_cookies(
            PHPSESSID="abc123", other="xyz"
        )

        result = get_codis_cookie()

        assert result is not None
        assert "PHPSESSID=abc123" in result
        assert "other=xyz" in result

    @patch(f"{MODULE}._codis_session")
    def test_returns_none_when_jar_empty(self, mock_session_factory: MagicMock) -> None:
        mock_session_factory.return_value = _session_with_cookies()

        assert get_codis_cookie() is None

    @patch(f"{MODULE}._codis_session")
    def test_returns_none_on_request_error(
        self, mock_session_factory: MagicMock
    ) -> None:
        session = _session_with_cookies(PHPSESSID="abc")
        session.get.side_effect = requests.exceptions.SSLError("strict x509")
        mock_session_factory.return_value = session

        assert get_codis_cookie() is None


class TestValidateCookie:
    @patch(f"{MODULE}._codis_session")
    def test_true_when_status_200(self, mock_session_factory: MagicMock) -> None:
        mock_session_factory.return_value = _session_with_cookies()

        assert validate_cookie("PHPSESSID=abc") is True

    @patch(f"{MODULE}._codis_session")
    def test_false_when_status_not_200(self, mock_session_factory: MagicMock) -> None:
        session = _session_with_cookies()
        session.post.return_value.status_code = 403
        mock_session_factory.return_value = session

        assert validate_cookie("PHPSESSID=abc") is False

    @patch(f"{MODULE}._codis_session")
    def test_false_on_request_error(self, mock_session_factory: MagicMock) -> None:
        session = _session_with_cookies()
        session.post.side_effect = requests.exceptions.Timeout("timeout")
        mock_session_factory.return_value = session

        assert validate_cookie("PHPSESSID=abc") is False


class TestGetValidCookie:
    @patch(f"{MODULE}.time.sleep")
    @patch(f"{MODULE}.validate_cookie", return_value=True)
    @patch(f"{MODULE}.get_codis_cookie", return_value="PHPSESSID=abc")
    def test_fetches_and_reuses_cache(
        self,
        mock_get: MagicMock,
        mock_validate: MagicMock,
        mock_sleep: MagicMock,
    ) -> None:
        first = get_valid_cookie()
        second = get_valid_cookie()

        assert first == "PHPSESSID=abc"
        assert second == "PHPSESSID=abc"
        assert mock_get.call_count == 1
        mock_sleep.assert_not_called()

    @patch(f"{MODULE}.time.sleep")
    @patch(f"{MODULE}.validate_cookie", side_effect=[False, True])
    @patch(f"{MODULE}.get_codis_cookie", return_value="PHPSESSID=retry")
    def test_retries_until_valid(
        self,
        mock_get: MagicMock,
        mock_validate: MagicMock,
        mock_sleep: MagicMock,
    ) -> None:
        result = get_valid_cookie()

        assert result == "PHPSESSID=retry"
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once_with(2)

    @patch(f"{MODULE}.time.sleep")
    @patch(f"{MODULE}.validate_cookie", return_value=False)
    @patch(f"{MODULE}.get_codis_cookie", return_value="PHPSESSID=bad")
    def test_raises_after_retries(
        self,
        mock_get: MagicMock,
        mock_validate: MagicMock,
        mock_sleep: MagicMock,
    ) -> None:
        with pytest.raises(Exception, match="無法取得有效的 Cookie"):
            get_valid_cookie()

        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 3
