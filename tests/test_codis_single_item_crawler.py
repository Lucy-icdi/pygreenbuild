"""單項逐時月報表／逐日年報表／逐月年報表與 resolve_item 單元測試（mock 網路）。"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pygreenbuild.ingestion.weather_crawler.codis_single_item_crawler import (
    ONE_DATE_ITEMS,
    ONE_MONTH_ITEMS,
    ONE_YEAR_ITEMS,
    _fetch_single_item,
    _unwrap_station_payload,
    codis_single_daily_yearly,
    codis_single_hourly_monthly,
    codis_single_monthly_yearly,
    resolve_item,
)

MODULE = "pygreenbuild.ingestion.weather_crawler.codis_single_item_crawler"
SAMPLE_DTS = [
    {
        "DateTime": "2026-03-01T01:00:00",
        "SeaLevelPressure": {"Instantaneous": 1013.1, "Instantaneousf": None},
    }
]


# ---------------------------------------------------------------------------
# resolve_item
# ---------------------------------------------------------------------------


class TestResolveItem:
    def test_exact_value(self) -> None:
        ok, value, message = resolve_item("SeaLevelPressure")
        assert ok is True
        assert value == "SeaLevelPressure"
        assert "SeaLevelPressure" in message

    def test_exact_value_case_insensitive(self) -> None:
        ok, value, _message = resolve_item("sealevelpressure")
        assert ok is True
        assert value == "SeaLevelPressure"

    def test_exact_key(self) -> None:
        ok, value, message = resolve_item("海平面氣壓(hPa)")
        assert ok is True
        assert value == "SeaLevelPressure"
        assert "海平面氣壓(hPa)" in message

    def test_regex_single_match(self) -> None:
        ok, value, _message = resolve_item("氣溫")
        assert ok is True
        assert value == "AirTemperature"

    def test_regex_multiple_defaults_to_first(self) -> None:
        ok, value, message = resolve_item("氣壓")
        assert ok is True
        assert value == "StationPressure"
        assert "第 1/2" in message

    def test_regex_multiple_select_second(self) -> None:
        ok, value, message = resolve_item("氣壓", 2)
        assert ok is True
        assert value == "SeaLevelPressure"
        assert "第 2/2" in message

    def test_regex_visibility_second_is_auto(self) -> None:
        ok, value, _message = resolve_item("能見度", 2)
        assert ok is True
        assert value == "VisibilityAuto"

    def test_match_index_none_is_first(self) -> None:
        ok, value, _message = resolve_item("地溫", None)
        assert ok is True
        assert value == "SoilTemperatureAt0cm"

    def test_match_index_out_of_range(self) -> None:
        ok, value, message = resolve_item("氣壓", 9)
        assert ok is False
        assert value is None
        assert "超出範圍" in message
        assert "測站氣壓" in message
        assert "海平面氣壓" in message

    def test_match_index_must_be_positive(self) -> None:
        ok, value, message = resolve_item("氣溫", 0)
        assert ok is False
        assert value is None
        assert "大於等於 1" in message

    def test_empty_item(self) -> None:
        ok, value, message = resolve_item("  ")
        assert ok is False
        assert value is None
        assert "請提供" in message

    def test_invalid_regex(self) -> None:
        ok, value, message = resolve_item("氣溫(")
        assert ok is False
        assert value is None
        assert "正則表達式無效" in message

    def test_no_match(self) -> None:
        ok, value, message = resolve_item("不存在的要素")
        assert ok is False
        assert value is None
        assert "找不到符合的觀測要素" in message
        assert "氣溫(℃)" in message

    def test_passthrough_unknown_api_code(self) -> None:
        ok, value, message = resolve_item("CustomApiItem")
        assert ok is True
        assert value == "CustomApiItem"
        assert "CustomApiItem" in message

    def test_wind_speed_value_with_comma(self) -> None:
        ok, value, _message = resolve_item("WindSpeed,WindDirection")
        assert ok is True
        assert value == "WindSpeed,WindDirection"

    def test_custom_mapping(self) -> None:
        ok, value, _message = resolve_item("foo", mapping={"foo_bar": "FooBar"})
        assert ok is True
        assert value == "FooBar"


# ---------------------------------------------------------------------------
# _unwrap_station_payload
# ---------------------------------------------------------------------------


class TestUnwrapStationPayload:
    def test_hour_wrapper(self) -> None:
        raw = {"hour": {"code": 200, "data": [{"dts": SAMPLE_DTS}]}}
        unwrapped = _unwrap_station_payload(raw)
        assert unwrapped is not None
        assert unwrapped["data"][0]["dts"] == SAMPLE_DTS

    def test_top_level_data(self) -> None:
        raw = {"data": [{"dts": SAMPLE_DTS}]}
        unwrapped = _unwrap_station_payload(raw)
        assert unwrapped is not None
        assert unwrapped["data"][0]["dts"] == SAMPLE_DTS

    def test_invalid(self) -> None:
        assert _unwrap_station_payload("not-a-dict") is None
        assert _unwrap_station_payload({"hour": {"code": 200}}) is None


# ---------------------------------------------------------------------------
# codis_single_hourly_monthly
# ---------------------------------------------------------------------------


class TestCodisSingleHourlyMonthly:
    @patch(f"{MODULE}._fetch_single_item")
    def test_default_returns_python_object_without_saving(
        self, mock_fetch: MagicMock, tmp_path: Path
    ) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        success, data, message = codis_single_hourly_monthly(
            "466900", "2026-03", "SeaLevelPressure"
        )

        assert success is True
        assert data == SAMPLE_DTS
        assert "下載成功" in message
        assert list(tmp_path.iterdir()) == []

    def test_invalid_item(self) -> None:
        success, data, message = codis_single_hourly_monthly(
            "466900", "2026-03", "不存在的要素"
        )
        assert success is False
        assert data is None
        assert "找不到符合的觀測要素" in message

    def test_invalid_date_format(self) -> None:
        success, data, message = codis_single_hourly_monthly(
            "466900", "2026/03", "氣溫"
        )
        assert success is False
        assert data is None
        assert "日期格式錯誤" in message

    @pytest.mark.parametrize(
        "set_ym, start, end",
        [
            ("202603", "2026-03-01T00:00:00", "2026-03-31T23:59:59"),
            ("2026-03", "2026-03-01T00:00:00", "2026-03-31T23:59:59"),
            ("2026-02-15", "2026-02-01T00:00:00", "2026-02-28T23:59:59"),
        ],
    )
    @patch(f"{MODULE}._fetch_single_item")
    def test_date_range_and_payload(
        self,
        mock_fetch: MagicMock,
        set_ym: str,
        start: str,
        end: str,
    ) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        success, data, message = codis_single_hourly_monthly(
            "466900", set_ym, "海平面氣壓(hPa)"
        )

        assert success is True
        assert data == SAMPLE_DTS
        payload = mock_fetch.call_args.args[0]
        assert payload["type"] == "one_date"
        assert payload["stn_ID"] == "466900"
        assert payload["stn_type"] == "cwb"
        assert payload["item"] == "SeaLevelPressure"
        assert payload["start"] == start
        assert payload["end"] == end
        assert payload["date"] == f"{start}+08:00"
        assert "海平面氣壓(hPa)" in message

    @patch(f"{MODULE}._fetch_single_item")
    def test_saves_json_when_return_data_is_path(
        self, mock_fetch: MagicMock, tmp_path: Path
    ) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        success, data, message = codis_single_hourly_monthly(
            "466900", "2026-03", "SeaLevelPressure", return_data=str(tmp_path)
        )

        assert success is True
        assert data == SAMPLE_DTS
        out = tmp_path / "202603_466900_SeaLevelPressure.json"
        assert out.exists()
        assert json.loads(out.read_text(encoding="utf-8")) == SAMPLE_DTS
        assert "下載成功" in message

    @patch(f"{MODULE}._fetch_single_item")
    def test_empty_return_data_does_not_save(
        self, mock_fetch: MagicMock, tmp_path: Path
    ) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        success, data, _message = codis_single_hourly_monthly(
            "466900", "2026-03", "SeaLevelPressure", return_data="  "
        )

        assert success is True
        assert data == SAMPLE_DTS
        assert list(tmp_path.iterdir()) == []

    @patch(f"{MODULE}._fetch_single_item")
    def test_wind_filename_replaces_comma(
        self, mock_fetch: MagicMock, tmp_path: Path
    ) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        success, data, _message = codis_single_hourly_monthly(
            "466900", "2026-03", "風速", return_data=str(tmp_path)
        )

        assert success is True
        assert data == SAMPLE_DTS
        assert (tmp_path / "202603_466900_WindSpeed_WindDirection.json").exists()

    @patch(f"{MODULE}._fetch_single_item")
    def test_match_index_selects_second_key(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        codis_single_hourly_monthly("466900", "2026-03", "氣壓", 2)

        assert mock_fetch.call_args.args[0]["item"] == "SeaLevelPressure"

    @patch(f"{MODULE}._fetch_single_item")
    def test_auto_station_type(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        codis_single_hourly_monthly("C0A520", "2026-03", "氣溫")

        assert mock_fetch.call_args.args[0]["stn_type"] == "auto_C0"

    @patch(f"{MODULE}._fetch_single_item")
    def test_fetch_failure_propagates(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (False, None, "API 回傳格式不符預期")

        success, data, message = codis_single_hourly_monthly(
            "466900", "2026-03", "氣溫"
        )

        assert success is False
        assert data is None
        assert message == "API 回傳格式不符預期"

    def test_one_date_mapping_covers_expected_keys(self) -> None:
        assert ONE_DATE_ITEMS["紫外線指數"] == "UVIndex"
        assert "測站最高氣壓(hPa) / 測站最高氣壓時間(LST)" not in ONE_DATE_ITEMS

    @patch(f"{MODULE}.get_valid_cookie", return_value="session=fake")
    @patch(f"{MODULE}.requests.post")
    def test_fetch_parses_hour_wrapped_json(
        self, mock_post: MagicMock, _mock_cookie: MagicMock
    ) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "hour": {
                "code": 200,
                "data": [{"StationID": "466900", "dts": SAMPLE_DTS}],
            }
        }
        mock_post.return_value = mock_response

        success, data, message = _fetch_single_item({"item": "SeaLevelPressure"})
        assert success is True
        assert data == SAMPLE_DTS
        assert message == "下載成功"


# ---------------------------------------------------------------------------
# codis_single_daily_yearly
# ---------------------------------------------------------------------------


class TestCodisSingleDailyYearly:
    def test_invalid_item(self) -> None:
        success, data, message = codis_single_daily_yearly(
            "466930", 2026, "不存在的要素"
        )
        assert success is False
        assert data is None
        assert "找不到符合的觀測要素" in message

    def test_invalid_year_format(self) -> None:
        success, data, message = codis_single_daily_yearly(
            "466930", "2026/01", "氣溫"
        )
        assert success is False
        assert data is None
        assert "年份格式錯誤" in message

    def test_one_month_mapping_has_annual_only_items(self) -> None:
        ok, value, _message = resolve_item("最高氣溫", mapping=ONE_MONTH_ITEMS)
        assert ok is True
        assert value == "MaxAirTemperature"
        assert ONE_MONTH_ITEMS["日照率(%)"] == "SunshineDurationRate"
        assert "紫外線指數" not in ONE_MONTH_ITEMS

    @pytest.mark.parametrize(
        "year, start, end",
        [
            (2026, "2026-01-01T00:00:00", "2026-12-31T00:00:00"),
            ("2026", "2026-01-01T00:00:00", "2026-12-31T00:00:00"),
            ("202603", "2026-01-01T00:00:00", "2026-12-31T00:00:00"),
            ("2026-03-15", "2026-01-01T00:00:00", "2026-12-31T00:00:00"),
        ],
    )
    @patch(f"{MODULE}._fetch_single_item")
    def test_year_range_and_payload(
        self,
        mock_fetch: MagicMock,
        year: int | str,
        start: str,
        end: str,
    ) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        success, data, message = codis_single_daily_yearly(
            "466930", year, "海平面氣壓(hPa)"
        )

        assert success is True
        assert data == SAMPLE_DTS
        payload = mock_fetch.call_args.args[0]
        assert payload["type"] == "one_month"
        assert payload["stn_ID"] == "466930"
        assert payload["stn_type"] == "cwb"
        assert payload["item"] == "SeaLevelPressure"
        assert payload["start"] == start
        assert payload["end"] == end
        assert payload["date"] == f"{start}+08:00"
        assert "海平面氣壓(hPa)" in message

    @patch(f"{MODULE}._fetch_single_item")
    def test_saves_json_when_return_data_is_path(
        self, mock_fetch: MagicMock, tmp_path: Path
    ) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        success, data, message = codis_single_daily_yearly(
            "466930", 2026, "SeaLevelPressure", return_data=str(tmp_path)
        )

        assert success is True
        assert data == SAMPLE_DTS
        out = tmp_path / "2026_466930_SeaLevelPressure.json"
        assert out.exists()
        assert json.loads(out.read_text(encoding="utf-8")) == SAMPLE_DTS
        assert "下載成功" in message

    @patch(f"{MODULE}._fetch_single_item")
    def test_default_does_not_save(self, mock_fetch: MagicMock, tmp_path: Path) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        success, data, _message = codis_single_daily_yearly(
            "466930", 2026, "SeaLevelPressure"
        )

        assert success is True
        assert data == SAMPLE_DTS
        assert list(tmp_path.iterdir()) == []

    @patch(f"{MODULE}._fetch_single_item")
    def test_match_index_selects_second_key(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        codis_single_daily_yearly("466930", 2026, "氣壓", 2)

        assert mock_fetch.call_args.args[0]["item"] == "SeaLevelPressure"

    @patch(f"{MODULE}._fetch_single_item")
    def test_max_air_temperature_item(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        codis_single_daily_yearly("466930", 2026, "最高氣溫")

        assert mock_fetch.call_args.args[0]["item"] == "MaxAirTemperature"

    @patch(f"{MODULE}._fetch_single_item")
    def test_auto_station_type(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        codis_single_daily_yearly("C0A520", 2026, "氣溫")

        assert mock_fetch.call_args.args[0]["stn_type"] == "auto_C0"

    @patch(f"{MODULE}._fetch_single_item")
    def test_fetch_failure_propagates(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (False, None, "API 回傳格式不符預期")

        success, data, message = codis_single_daily_yearly("466930", 2026, "氣溫")

        assert success is False
        assert data is None
        assert message == "API 回傳格式不符預期"


# ---------------------------------------------------------------------------
# codis_single_monthly_yearly
# ---------------------------------------------------------------------------


class TestCodisSingleMonthlyYearly:
    def test_invalid_item(self) -> None:
        success, data, message = codis_single_monthly_yearly(
            "466930", 2026, "不存在的要素"
        )
        assert success is False
        assert data is None
        assert "找不到符合的觀測要素" in message

    def test_invalid_year_format(self) -> None:
        success, data, message = codis_single_monthly_yearly(
            "466930", "2026/01", "氣溫"
        )
        assert success is False
        assert data is None
        assert "年份格式錯誤" in message

    def test_one_year_mapping_has_monthly_only_items(self) -> None:
        ok, value, _message = resolve_item("降水日數", mapping=ONE_YEAR_ITEMS)
        assert ok is True
        assert value == "PrecipitationDays"
        assert ONE_YEAR_ITEMS["平均日最高紫外線指數"] == "MaxMeanUVIndex"
        assert ONE_YEAR_ITEMS["最大日降雨量(mm)/最大日降雨量時間(LST)"] == (
            "MaxDailyPrecipitation"
        )
        assert "紫外線指數" not in ONE_YEAR_ITEMS
        assert "日照率(%)" not in ONE_YEAR_ITEMS

    @pytest.mark.parametrize(
        "year, start, end",
        [
            (2026, "2026-01-01T00:00:00", "2026-12-31T00:00:00"),
            ("2026", "2026-01-01T00:00:00", "2026-12-31T00:00:00"),
            ("202603", "2026-01-01T00:00:00", "2026-12-31T00:00:00"),
            ("2026-03-15", "2026-01-01T00:00:00", "2026-12-31T00:00:00"),
        ],
    )
    @patch(f"{MODULE}._fetch_single_item")
    def test_year_range_and_payload(
        self,
        mock_fetch: MagicMock,
        year: int | str,
        start: str,
        end: str,
    ) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        success, data, message = codis_single_monthly_yearly(
            "466930", year, "測站氣壓(hPa)"
        )

        assert success is True
        assert data == SAMPLE_DTS
        payload = mock_fetch.call_args.args[0]
        assert payload["type"] == "one_year"
        assert payload["stn_ID"] == "466930"
        assert payload["stn_type"] == "cwb"
        assert payload["item"] == "StationPressure"
        assert payload["start"] == start
        assert payload["end"] == end
        assert payload["date"] == f"{start}+08:00"
        assert "測站氣壓(hPa)" in message

    @patch(f"{MODULE}._fetch_single_item")
    def test_saves_json_when_return_data_is_path(
        self, mock_fetch: MagicMock, tmp_path: Path
    ) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        success, data, message = codis_single_monthly_yearly(
            "466930", 2026, "StationPressure", return_data=str(tmp_path)
        )

        assert success is True
        assert data == SAMPLE_DTS
        out = tmp_path / "2026_466930_StationPressure_monthly.json"
        assert out.exists()
        assert json.loads(out.read_text(encoding="utf-8")) == SAMPLE_DTS
        assert "下載成功" in message

    @patch(f"{MODULE}._fetch_single_item")
    def test_default_does_not_save(self, mock_fetch: MagicMock, tmp_path: Path) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        success, data, _message = codis_single_monthly_yearly(
            "466930", 2026, "StationPressure"
        )

        assert success is True
        assert data == SAMPLE_DTS
        assert list(tmp_path.iterdir()) == []

    @patch(f"{MODULE}._fetch_single_item")
    def test_match_index_selects_second_key(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        codis_single_monthly_yearly("466930", 2026, "氣壓", 2)

        assert mock_fetch.call_args.args[0]["item"] == "SeaLevelPressure"

    @patch(f"{MODULE}._fetch_single_item")
    def test_precipitation_days_item(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        codis_single_monthly_yearly("466930", 2026, "降水日數")

        assert mock_fetch.call_args.args[0]["item"] == "PrecipitationDays"

    @patch(f"{MODULE}._fetch_single_item")
    def test_auto_station_type(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (True, SAMPLE_DTS, "下載成功")

        codis_single_monthly_yearly("C0A520", 2026, "氣溫")

        assert mock_fetch.call_args.args[0]["stn_type"] == "auto_C0"

    @patch(f"{MODULE}._fetch_single_item")
    def test_fetch_failure_propagates(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (False, None, "API 回傳格式不符預期")

        success, data, message = codis_single_monthly_yearly("466930", 2026, "氣溫")

        assert success is False
        assert data is None
        assert message == "API 回傳格式不符預期"
