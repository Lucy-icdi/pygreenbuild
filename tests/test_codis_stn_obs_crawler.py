"""codis_yearly／monthly／daily 單元測試（mock _fetch_data，不打真實網路）。"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from pygreenbuild.ingestion.weather_crawler.codis_stn_obs_crawler import (
    API_URL,
    _fetch_data,
    codis_daily,
    codis_monthly,
    codis_yearly,
)

MODULE = "pygreenbuild.ingestion.weather_crawler.codis_stn_obs_crawler"
SAMPLE_DTS = [{"DataTime": "2024-01-01T00:00:00", "AirTemperature": 20.0}]


def _session_post(response: MagicMock | None = None, *, side_effect: Exception | None = None) -> MagicMock:
    """建立可供 ``with _codis_session()`` 使用的假 session。"""
    session = MagicMock()
    session.__enter__.return_value = session
    session.__exit__.return_value = False
    if side_effect is not None:
        session.post.side_effect = side_effect
    else:
        session.post.return_value = response
    return session


class TestFetchData:
    @patch(f"{MODULE}._codis_session")
    @patch(f"{MODULE}.get_valid_cookie", return_value="PHPSESSID=fake")
    def test_posts_through_cwa_ssl_session(
        self, _mock_cookie: MagicMock, mock_session_factory: MagicMock
    ) -> None:
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"data": [{"dts": SAMPLE_DTS}]}
        session = _session_post(response)
        mock_session_factory.return_value = session

        success, data, message = _fetch_data({"type": "report_year"})

        assert success is True
        assert data == SAMPLE_DTS
        assert message == "下載成功"
        session.post.assert_called_once()
        assert session.post.call_args.args[0] == API_URL
        assert session.post.call_args.kwargs["headers"]["Cookie"] == "PHPSESSID=fake"
        assert session.post.call_args.kwargs["data"] == {"type": "report_year"}

    @patch(f"{MODULE}.get_valid_cookie", side_effect=Exception("cookie down"))
    def test_cookie_failure(self, _mock_cookie: MagicMock) -> None:
        success, data, message = _fetch_data({"type": "report_year"})

        assert success is False
        assert data is None
        assert message == "取得 Cookie 失敗: cookie down"

    @patch(f"{MODULE}._codis_session")
    @patch(f"{MODULE}.get_valid_cookie", return_value="PHPSESSID=fake")
    def test_ssl_error_is_network_error(
        self, _mock_cookie: MagicMock, mock_session_factory: MagicMock
    ) -> None:
        mock_session_factory.return_value = _session_post(
            side_effect=requests.exceptions.SSLError("CERTIFICATE_VERIFY_FAILED")
        )

        success, data, message = _fetch_data({"type": "report_year"})

        assert success is False
        assert data is None
        assert "發生網路錯誤" in message
        assert "CERTIFICATE_VERIFY_FAILED" in message

    @patch(f"{MODULE}._codis_session")
    @patch(f"{MODULE}.get_valid_cookie", return_value="PHPSESSID=fake")
    def test_http_error(
        self, _mock_cookie: MagicMock, mock_session_factory: MagicMock
    ) -> None:
        response = MagicMock()
        response.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
        mock_session_factory.return_value = _session_post(response)

        success, data, message = _fetch_data({"type": "report_year"})

        assert success is False
        assert data is None
        assert message.startswith("發生 HTTP 錯誤:")

    @patch(f"{MODULE}._codis_session")
    @patch(f"{MODULE}.get_valid_cookie", return_value="PHPSESSID=fake")
    def test_invalid_json(
        self, _mock_cookie: MagicMock, mock_session_factory: MagicMock
    ) -> None:
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.side_effect = json.JSONDecodeError("bad", "", 0)
        mock_session_factory.return_value = _session_post(response)

        success, data, message = _fetch_data({"type": "report_year"})

        assert success is False
        assert data is None
        assert "Cookie 無效" in message

    @patch(f"{MODULE}._codis_session")
    @patch(f"{MODULE}.get_valid_cookie", return_value="PHPSESSID=fake")
    def test_empty_or_unexpected_payload(
        self, _mock_cookie: MagicMock, mock_session_factory: MagicMock
    ) -> None:
        empty = MagicMock()
        empty.raise_for_status.return_value = None
        empty.json.return_value = {"data": [{"dts": []}]}
        mock_session_factory.return_value = _session_post(empty)

        success, data, message = _fetch_data({"type": "report_year"})
        assert success is False
        assert data is None
        assert message == "下載成功，但內容為空"

        unexpected = MagicMock()
        unexpected.raise_for_status.return_value = None
        unexpected.json.return_value = {"data": []}
        mock_session_factory.return_value = _session_post(unexpected)

        success, data, message = _fetch_data({"type": "report_year"})
        assert success is False
        assert data is None
        assert message == "API 回傳格式不符預期"


# ---------------------------------------------------------------------------
# codis_yearly
# ---------------------------------------------------------------------------


class TestCodisYearly:
    def test_requires_output_when_not_returning_data(self) -> None:
        success, message = codis_yearly("466920", None, 2024, return_data=False)
        assert success is False
        assert "output" in message

    @patch(f"{MODULE}._fetch_data")
    def test_return_data_without_saving(self, mock_fetch: MagicMock, tmp_path: Path) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        success, data, message = codis_yearly(
            "466920", None, 2024, return_data=True
        )

        assert success is True
        assert data == SAMPLE_DTS
        assert message == "下載成功"
        assert list(tmp_path.iterdir()) == []

        payload = mock_fetch.call_args.args[0]
        assert payload["type"] == "report_year"
        assert payload["stn_ID"] == "466920"
        assert payload["stn_type"] == "cwb"
        assert payload["start"] == "2024-01-01T00:00:00"
        assert payload["end"] == "2024-12-31T00:00:00"

    @patch(f"{MODULE}._fetch_data")
    def test_saves_json_when_output_dir_given(
        self, mock_fetch: MagicMock, tmp_path: Path
    ) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        success, message = codis_yearly(
            "466920", str(tmp_path), 2024, return_data=False
        )

        assert success is True
        assert message == "下載成功"
        out = tmp_path / "2024_466920.json"
        assert out.exists()
        assert json.loads(out.read_text(encoding="utf-8")) == SAMPLE_DTS

    @patch(f"{MODULE}._fetch_data")
    def test_saves_json_with_custom_filename(
        self, mock_fetch: MagicMock, tmp_path: Path
    ) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")
        custom = tmp_path / "cwa_466920.json"

        success, message = codis_yearly(
            "466920", str(custom), 2024, return_data=False
        )

        assert success is True
        assert message == "下載成功"
        assert custom.exists()
        assert not (tmp_path / "2024_466920.json").exists()
        assert json.loads(custom.read_text(encoding="utf-8")) == SAMPLE_DTS

    @patch(f"{MODULE}._fetch_data")
    def test_saves_json_with_bare_custom_filename(
        self, mock_fetch: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")
        monkeypatch.chdir(tmp_path)

        success, message = codis_yearly(
            "466920", "cwa_466920.json", 2024, return_data=False
        )

        assert success is True
        out = tmp_path / "cwa_466920.json"
        assert out.exists()
        assert json.loads(out.read_text(encoding="utf-8")) == SAMPLE_DTS

    @patch(f"{MODULE}._fetch_data")
    def test_auto_station_type(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        codis_yearly("C0A520", None, 2024, return_data=True)

        assert mock_fetch.call_args.args[0]["stn_type"] == "auto_C0"


# ---------------------------------------------------------------------------
# codis_monthly
# ---------------------------------------------------------------------------


class TestCodisMonthly:
    def test_requires_output_when_not_returning_data(self) -> None:
        success, message = codis_monthly("466920", None, "2024-11", return_data=False)
        assert success is False
        assert "output" in message

    @pytest.mark.parametrize(
        "set_ym, start, end, filename",
        [
            ("202411", "2024-11-01T00:00:00", "2024-11-30T00:00:00", "202411_466920.json"),
            ("2024-02", "2024-02-01T00:00:00", "2024-02-29T00:00:00", "202402_466920.json"),
            ("2024-11-15", "2024-11-01T00:00:00", "2024-11-30T00:00:00", "202411_466920.json"),
        ],
    )
    @patch(f"{MODULE}._fetch_data")
    def test_date_formats_and_month_range(
        self,
        mock_fetch: MagicMock,
        tmp_path: Path,
        set_ym: str,
        start: str,
        end: str,
        filename: str,
    ) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        success, message = codis_monthly(
            "466920", str(tmp_path), set_ym, return_data=False
        )

        assert success is True
        payload = mock_fetch.call_args.args[0]
        assert payload["type"] == "report_month"
        assert payload["start"] == start
        assert payload["end"] == end
        assert (tmp_path / filename).exists()

    def test_invalid_date_format_return_data(self) -> None:
        success, data, message = codis_monthly(
            "466920", None, "not-a-date", return_data=True
        )
        assert success is False
        assert data is None
        assert "日期格式錯誤" in message

    def test_invalid_date_format_export_mode(self) -> None:
        success, message = codis_monthly(
            "466920", "out", "2024/11", return_data=False
        )
        assert success is False
        assert "日期格式錯誤" in message


# ---------------------------------------------------------------------------
# codis_daily
# ---------------------------------------------------------------------------


class TestCodisDaily:
    def test_requires_output_when_not_returning_data(self) -> None:
        success, message = codis_daily("466920", None, "2024-11-01", return_data=False)
        assert success is False
        assert "output" in message

    def test_requires_at_least_one_date(self) -> None:
        success, data, message = codis_daily("466920", None, return_data=True)
        assert success is False
        assert data is None
        assert "至少提供一個日期" in message

    def test_invalid_date_format(self) -> None:
        success, message = codis_daily(
            "466920", "out", "2024/11/01", return_data=False
        )
        assert success is False
        assert "日期格式錯誤" in message

    def test_range_exceeds_31_days(self) -> None:
        success, data, message = codis_daily(
            "466920",
            None,
            "2024-01-01",
            "2024-02-15",
            return_data=True,
        )
        assert success is False
        assert data is None
        assert "31 天" in message

    @patch(f"{MODULE}._fetch_data")
    def test_single_day(self, mock_fetch: MagicMock, tmp_path: Path) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        success, message = codis_daily(
            "466920", str(tmp_path), "2024-11-01", return_data=False
        )

        assert success is True
        payload = mock_fetch.call_args.args[0]
        assert payload["type"] == "report_date"
        assert payload["start"] == "2024-11-01T00:00:00"
        assert payload["end"] == "2024-11-01T23:59:59"
        assert (tmp_path / "2024-11-01_466920.json").exists()

    @patch(f"{MODULE}._fetch_data")
    def test_date_range_unsorted_inputs(
        self, mock_fetch: MagicMock, tmp_path: Path
    ) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        success, data, message = codis_daily(
            "466920",
            str(tmp_path),
            "2024-11-30",
            "2024-11-01",
            return_data=True,
        )

        assert success is True
        assert data == SAMPLE_DTS
        payload = mock_fetch.call_args.args[0]
        assert payload["start"] == "2024-11-01T00:00:00"
        assert payload["end"] == "2024-11-30T23:59:59"
        assert (tmp_path / "2024-11-01~2024-11-30_466920.json").exists()

    @patch(f"{MODULE}._fetch_data")
    def test_fetch_failure_propagates(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (False, None, "API 回傳格式不符預期")

        success, data, message = codis_daily(
            "466920", None, "2024-11-01", return_data=True
        )

        assert success is False
        assert data is None
        assert message == "API 回傳格式不符預期"
