"""transform.json_to_dataframe 單元測試。"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from pygreenbuild.transform import json_to_dataframe


def _is_na(value: object) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or pd.isna(value)


class TestJsonToDataframeHour:
    def test_nested_fields_and_chinese_columns(self) -> None:
        data = [
            {
                "DataTime": "2025-08-15T14:00:00",
                "AirTemperature": {"Instantaneous": 28.5},
                "RelativeHumidity": {"Instantaneous": 70},
                "Precipitation": {"Accumulation": 1.2},
            }
        ]
        out = json_to_dataframe(data)
        assert out["觀測時間"].iloc[0] == "2025-08-15T14:00:00"
        assert out["氣溫"].iloc[0] == 28.5
        assert out["相對溼度"].iloc[0] == 70
        assert out["降水量"].iloc[0] == 1.2
        # 對應表路徑為 None 或整欄空白的欄位會被刪除
        assert "濕球溫度" not in out.columns
        assert "雲冪高" not in out.columns

    def test_2359_rolls_to_next_day(self) -> None:
        data = [
            {
                "DataTime": "2025-08-15T23:59:00",
                "AirTemperature": {"Instantaneous": 26.0},
            }
        ]
        out = json_to_dataframe(data)
        assert out["觀測時間"].iloc[0] == "2025-08-16T00:00:00"

    def test_2359_with_seconds_rolls_to_midnight(self) -> None:
        data = [
            {
                "DataTime": "2025-08-15T23:59:30",
                "AirTemperature": {"Instantaneous": 26.0},
            }
        ]
        out = json_to_dataframe(data)
        assert out["觀測時間"].iloc[0] == "2025-08-16T00:00:00"

    def test_trace_precipitation(self) -> None:
        data = [
            {
                "DataTime": "2025-08-15T14:00:00",
                "Precipitation": {"Accumulation": "T"},
            }
        ]
        out = json_to_dataframe(data)
        assert out["降水量"].iloc[0] == 0.4

    def test_na_sentinel_values_drop_all_na_columns(self) -> None:
        data = [
            {
                "DataTime": "2025-08-15T14:00:00",
                "AirTemperature": {"Instantaneous": -99},
                "WindSpeed": {"Mean": "x"},
                "RelativeHumidity": {"Instantaneous": 70},
            }
        ]
        out = json_to_dataframe(data)
        assert "氣溫" not in out.columns
        assert "風速" not in out.columns
        assert out["相對溼度"].iloc[0] == 70

    def test_temp_below_minus_50_masked(self) -> None:
        data = [
            {
                "DataTime": "2025-08-15T14:00:00",
                "AirTemperature": {"Instantaneous": -51},
                "RelativeHumidity": {"Instantaneous": 60},
            }
        ]
        out = json_to_dataframe(data)
        assert "氣溫" not in out.columns
        assert out["相對溼度"].iloc[0] == 60

    def test_non_temp_negative_masked(self) -> None:
        data = [
            {
                "DataTime": "2025-08-15T14:00:00",
                "WindSpeed": {"Mean": -1},
                "RelativeHumidity": {"Instantaneous": 55},
            }
        ]
        out = json_to_dataframe(data)
        assert "風速" not in out.columns
        assert out["相對溼度"].iloc[0] == 55

    def test_drops_all_na_columns(self) -> None:
        data = [
            {
                "DataTime": "2025-08-15T14:00:00",
                "AirTemperature": {"Instantaneous": 28.5},
            },
            {
                "DataTime": "2025-08-15T15:00:00",
                "AirTemperature": {"Instantaneous": None},
            },
        ]
        out = json_to_dataframe(data)
        assert "氣溫" in out.columns
        assert out["氣溫"].iloc[0] == 28.5
        assert _is_na(out["氣溫"].iloc[1])
        assert "濕球溫度" not in out.columns

    def test_missing_unified_to_pd_na(self) -> None:
        data = [
            {
                "DataTime": "2025-08-15T14:00:00",
                "AirTemperature": {"Instantaneous": 28.5},
                "RelativeHumidity": {"Instantaneous": float("nan")},
            },
            {
                "DataTime": "2025-08-15T15:00:00",
                "AirTemperature": {"Instantaneous": None},
                "RelativeHumidity": {"Instantaneous": 70},
            },
        ]
        out = json_to_dataframe(data)
        temp_na = out["氣溫"].iloc[1]
        rh_na = out["相對溼度"].iloc[0]
        assert pd.isna(temp_na)
        assert pd.isna(rh_na)
        assert temp_na is pd.NA
        assert rh_na is pd.NA
        assert not isinstance(rh_na, float)


class TestJsonToDataframeDayMonth:
    def test_day_format(self) -> None:
        data = [
            {
                "DataDate": "2025-08-15",
                "AirTemperature": {
                    "Mean": 27.0,
                    "Maximum": 32.0,
                    "Minimum": 24.0,
                },
            }
        ]
        out = json_to_dataframe(data)
        assert out["觀測時間"].iloc[0] == "2025-08-15T00:00:00"
        assert out["氣溫"].iloc[0] == 27.0
        assert out["最高氣溫"].iloc[0] == 32.0
        assert out["最低氣溫"].iloc[0] == 24.0

    def test_month_format(self) -> None:
        data = [
            {
                "DataYearMonth": "2025-08",
                "AirTemperature": {"Mean": 28.0},
                "Precipitation": {"Accumulation": 120.5},
            }
        ]
        out = json_to_dataframe(data)
        assert out["觀測月份"].iloc[0] == "2025-08"
        assert out["氣溫"].iloc[0] == 28.0
        assert out["降水量"].iloc[0] == 120.5


class TestJsonToDataframeCustomMapping:
    def test_custom_mapping(self) -> None:
        data = [
            {
                "DataTime": "2025-08-15T14:00:00",
                "AirTemperature": {"Instantaneous": 28.5},
            }
        ]
        out = json_to_dataframe(
            data,
            column_mapping={
                "觀測時間": "DataTime",
                "氣溫": "AirTemperature.Instantaneous",
            },
        )
        assert list(out.columns) == ["觀測時間", "氣溫"]
        assert out["氣溫"].iloc[0] == 28.5

    def test_missing_path_column_dropped(self) -> None:
        data = [{"DataTime": "2025-08-15T14:00:00"}]
        out = json_to_dataframe(
            data,
            column_mapping={
                "觀測時間": "DataTime",
                "氣溫": "AirTemperature.Instantaneous",
            },
        )
        assert list(out.columns) == ["觀測時間"]
        assert "氣溫" not in out.columns

    def test_empty_data_raises_without_mapping(self) -> None:
        with pytest.raises(ValueError, match="資料為空"):
            json_to_dataframe([])

    def test_unknown_format_raises(self) -> None:
        with pytest.raises(ValueError, match="未知資料格式"):
            json_to_dataframe([{"foo": 1}])
