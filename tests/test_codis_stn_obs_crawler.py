"""codis_yearly／monthly／daily 單元測試（mock _fetch_data，不打真實網路）。"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pygreenbuild.ingestion.weather_crawler.codis_stn_obs_crawler import (
    codis_daily,
    codis_monthly,
    codis_yearly,
)

MODULE = "pygreenbuild.ingestion.weather_crawler.codis_stn_obs_crawler"
SAMPLE_DTS = [{"DataTime": "2024-01-01T00:00:00", "AirTemperature": 20.0}]


# ---------------------------------------------------------------------------
# codis_yearly
# ---------------------------------------------------------------------------


class TestCodisYearly:
    def test_requires_output_dir_when_not_returning_data(self) -> None:
        success, message = codis_yearly("466920", None, 2024, return_data=False)
        assert success is False
        assert "output_dir" in message

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
    def test_auto_station_type(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        codis_yearly("C0A520", None, 2024, return_data=True)

        assert mock_fetch.call_args.args[0]["stn_type"] == "auto_C0"


# ---------------------------------------------------------------------------
# codis_monthly
# ---------------------------------------------------------------------------


class TestCodisMonthly:
    def test_requires_output_dir_when_not_returning_data(self) -> None:
        success, message = codis_monthly("466920", None, "2024-11", return_data=False)
        assert success is False
        assert "output_dir" in message

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
    def test_requires_output_dir_when_not_returning_data(self) -> None:
        success, message = codis_daily("466920", None, "2024-11-01", return_data=False)
        assert success is False
        assert "output_dir" in message

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
