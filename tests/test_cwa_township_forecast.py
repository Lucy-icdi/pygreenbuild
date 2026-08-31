"""cwa_township_forecast_3day／week 單元測試（mock HTTP，不打真實網路）。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from pygreenbuild.ingestion.weather_crawler.cwa_township_forecast import (
    COUNTY_DATASET_IDS,
    cwa_township_forecast_3day,
    cwa_township_forecast_week,
)

MODULE = "pygreenbuild.ingestion.weather_crawler.cwa_township_forecast"
API_KEY = "CWA-F8F425DD-TEST"
TOTAL_COUNTIES = len(COUNTY_DATASET_IDS)

SAMPLE_LOCATIONS = [
    {
        "LocationsName": "臺北市",
        "Location": [
            {
                "LocationName": "中正區",
                "WeatherElement": [
                    {
                        "ElementName": "溫度",
                        "Time": [
                            {
                                "DataTime": "2024-11-01T12:00:00+08:00",
                                "ElementValue": [{"Temperature": "26"}],
                            }
                        ],
                    }
                ],
            }
        ],
    }
]


def _response(payload: dict) -> MagicMock:
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = payload
    return mock_response


def _ok_payload(locations: list | None = None) -> dict:
    return {
        "success": "true",
        "records": {
            "Locations": locations if locations is not None else SAMPLE_LOCATIONS
        },
    }


def _requested_dataset_ids(mock_get: MagicMock) -> list[str]:
    return [call.args[0].rsplit("/", 1)[-1] for call in mock_get.call_args_list]


# ---------------------------------------------------------------------------
# 參數驗證
# ---------------------------------------------------------------------------


class TestArgumentValidation:
    def test_requires_output_dir_when_not_returning_data(self) -> None:
        success, message = cwa_township_forecast_3day(API_KEY, None)
        assert success is False
        assert "output_dir" in message

    @pytest.mark.parametrize("api_key", [None, "", "   "])
    def test_requires_api_key_export_mode(
        self, api_key: str | None, tmp_path: Path
    ) -> None:
        success, message = cwa_township_forecast_3day(api_key, str(tmp_path))
        assert success is False
        assert "缺少 CWA API 授權碼" in message

    def test_requires_api_key_return_data_mode(self) -> None:
        success, data, message = cwa_township_forecast_week(
            None, None, return_data=True
        )
        assert success is False
        assert data is None
        assert "缺少 CWA API 授權碼" in message

    @patch(f"{MODULE}.requests.get")
    def test_api_key_passed_to_request(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _response(_ok_payload())

        success, data, message = cwa_township_forecast_3day(
            f"  {API_KEY}  ", None, "臺北市", return_data=True
        )

        assert success is True
        assert data == SAMPLE_LOCATIONS
        assert mock_get.call_args.kwargs["params"]["Authorization"] == API_KEY

    @patch(f"{MODULE}.requests.get")
    def test_unknown_county_fails_before_request(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        success, message = cwa_township_forecast_3day(
            API_KEY, str(tmp_path), "火星市"
        )

        assert success is False
        assert "無法識別" in message
        mock_get.assert_not_called()
        assert list(tmp_path.iterdir()) == []

    @patch(f"{MODULE}.requests.get")
    def test_blank_county_fails(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        success, message = cwa_township_forecast_week(API_KEY, str(tmp_path), "  ")

        assert success is False
        assert "不可為空白" in message
        mock_get.assert_not_called()
        assert list(tmp_path.iterdir()) == []


# ---------------------------------------------------------------------------
# 縣市別／資料編號解析
# ---------------------------------------------------------------------------


class TestCountyResolution:
    @patch(f"{MODULE}.requests.get")
    def test_defaults_to_all_counties(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        mock_get.return_value = _response(_ok_payload())

        success, message = cwa_township_forecast_3day(API_KEY, str(tmp_path))

        assert success is True
        assert mock_get.call_count == TOTAL_COUNTIES
        assert _requested_dataset_ids(mock_get) == [
            ids[0] for ids in COUNTY_DATASET_IDS.values()
        ]
        assert len(list(tmp_path.iterdir())) == TOTAL_COUNTIES

    @patch(f"{MODULE}.requests.get")
    def test_week_defaults_to_all_counties(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        mock_get.return_value = _response(_ok_payload())

        cwa_township_forecast_week(API_KEY, str(tmp_path))

        assert _requested_dataset_ids(mock_get) == [
            ids[1] for ids in COUNTY_DATASET_IDS.values()
        ]

    @pytest.mark.parametrize(
        "target",
        ["臺北市", "台北市", "  臺北市  ", "F-D0047-061", "f-d0047-061", "F_D0047_061"],
    )
    @patch(f"{MODULE}.requests.get")
    def test_single_county_by_name_or_dataset_id(
        self, mock_get: MagicMock, target: str, tmp_path: Path
    ) -> None:
        mock_get.return_value = _response(_ok_payload())

        success, message = cwa_township_forecast_3day(
            API_KEY, str(tmp_path), target
        )

        assert success is True
        assert _requested_dataset_ids(mock_get) == ["F-D0047-061"]

    @patch(f"{MODULE}.requests.get")
    def test_dataset_id_identifies_county_only(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        """傳入 1 週編號給 3 天爬蟲，會下載同一縣市的 3 天資料集。"""
        mock_get.return_value = _response(_ok_payload())

        cwa_township_forecast_3day(API_KEY, str(tmp_path), "F-D0047-083")

        assert _requested_dataset_ids(mock_get) == ["F-D0047-081"]

    @patch(f"{MODULE}.requests.get")
    def test_multiple_counties_deduplicated(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        mock_get.return_value = _response(_ok_payload())

        cwa_township_forecast_week(
            API_KEY, str(tmp_path), "臺北市", "F-D0047-063", "宜蘭縣"
        )

        assert _requested_dataset_ids(mock_get) == ["F-D0047-063", "F-D0047-003"]


# ---------------------------------------------------------------------------
# 寫檔與回傳
# ---------------------------------------------------------------------------


class TestOutput:
    @patch(f"{MODULE}.requests.get")
    def test_saves_one_file_per_county(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        mock_get.return_value = _response(_ok_payload())
        today = datetime.now().strftime("%Y-%m-%d")

        success, message = cwa_township_forecast_3day(
            API_KEY, str(tmp_path), "臺北市", "宜蘭縣"
        )

        assert success is True
        taipei = tmp_path / f"{today}_township_3day_臺北市.json"
        yilan = tmp_path / f"{today}_township_3day_宜蘭縣.json"
        assert taipei.exists()
        assert yilan.exists()
        assert json.loads(taipei.read_text(encoding="utf-8")) == SAMPLE_LOCATIONS

    @patch(f"{MODULE}.requests.get")
    def test_week_filename_suffix(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        mock_get.return_value = _response(_ok_payload())
        today = datetime.now().strftime("%Y-%m-%d")

        cwa_township_forecast_week(API_KEY, str(tmp_path), "連江縣")

        assert (tmp_path / f"{today}_township_week_連江縣.json").exists()

    @patch(f"{MODULE}.requests.get")
    def test_return_data_without_saving(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        mock_get.return_value = _response(_ok_payload())

        success, data, message = cwa_township_forecast_3day(
            API_KEY, None, "臺北市", return_data=True
        )

        assert success is True
        assert data == SAMPLE_LOCATIONS
        assert list(tmp_path.iterdir()) == []

    @patch(f"{MODULE}.requests.get")
    def test_return_data_collects_every_county(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _response(_ok_payload())

        success, data, message = cwa_township_forecast_week(
            API_KEY, None, "臺北市", "宜蘭縣", return_data=True
        )

        assert success is True
        assert data is not None
        assert len(data) == 2
        assert message == "下載成功：2 個縣市"


# ---------------------------------------------------------------------------
# 失敗情境
# ---------------------------------------------------------------------------


class TestFailures:
    @patch(f"{MODULE}.requests.get")
    def test_api_reports_failure(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _response({"success": "false"})

        success, data, message = cwa_township_forecast_3day(
            API_KEY, None, "臺北市", return_data=True
        )

        assert success is False
        assert data is None
        assert "API 回報失敗" in message

    @patch(f"{MODULE}.requests.get")
    def test_unexpected_structure(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _response({"success": "true", "records": []})

        success, data, message = cwa_township_forecast_3day(
            API_KEY, None, "臺北市", return_data=True
        )

        assert success is False
        assert data is None
        assert "格式不符預期" in message

    @patch(f"{MODULE}.requests.get")
    def test_empty_locations(self, mock_get: MagicMock, tmp_path: Path) -> None:
        mock_get.return_value = _response(_ok_payload([]))

        success, message = cwa_township_forecast_3day(
            API_KEY, str(tmp_path), "臺北市"
        )

        assert success is False
        assert "內容為空" in message
        assert list(tmp_path.iterdir()) == []

    @patch(f"{MODULE}.requests.get")
    def test_unauthorized(self, mock_get: MagicMock) -> None:
        error_response = MagicMock()
        error_response.status_code = 401
        mock_get.return_value.raise_for_status.side_effect = (
            requests.exceptions.HTTPError("401 Client Error", response=error_response)
        )

        success, data, message = cwa_township_forecast_week(
            API_KEY, None, "臺北市", return_data=True
        )

        assert success is False
        assert data is None
        assert "授權失敗" in message

    @patch(f"{MODULE}.requests.get")
    def test_network_error(self, mock_get: MagicMock, tmp_path: Path) -> None:
        mock_get.side_effect = requests.exceptions.ConnectionError("boom")

        success, message = cwa_township_forecast_3day(
            API_KEY, str(tmp_path), "臺北市"
        )

        assert success is False
        assert "網路錯誤" in message
        assert list(tmp_path.iterdir()) == []

    @patch(f"{MODULE}.requests.get")
    def test_partial_failure_keeps_successful_counties(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        mock_get.side_effect = [
            _response(_ok_payload()),
            requests.exceptions.ConnectionError("boom"),
        ]
        today = datetime.now().strftime("%Y-%m-%d")

        success, data, message = cwa_township_forecast_3day(
            API_KEY, str(tmp_path), "臺北市", "宜蘭縣", return_data=True
        )

        assert success is False
        assert data == SAMPLE_LOCATIONS
        assert "下載完成 1/2 個縣市" in message
        assert "宜蘭縣（F-D0047-001）" in message
        assert (tmp_path / f"{today}_township_3day_臺北市.json").exists()
        assert not (tmp_path / f"{today}_township_3day_宜蘭縣.json").exists()
