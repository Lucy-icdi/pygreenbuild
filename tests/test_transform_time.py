"""transform.transform_time 單元測試。"""

from __future__ import annotations

from datetime import date, datetime, time

import pandas as pd
import pytest

from pygreenbuild.transform import (
    to_date_column,
    to_datetime_column,
    to_time_column,
)


class TestToDateColumn:
    def test_mixed_formats(self) -> None:
        df = pd.DataFrame(
            {
                "d": [
                    "2025/08/15",
                    "2025/8/15",
                    "2025-08-15",
                    "2025-8-15",
                    "20250815",
                ]
            }
        )
        out = to_date_column(df, "d")
        assert all(v == date(2025, 8, 15) for v in out["d"])
        assert df["d"].dtype == object

    def test_from_datetime_string(self) -> None:
        df = pd.DataFrame(
            {
                "d": [
                    "2025-08-15 14:00:15",
                    "2025-08-15T14:00:15",
                    "2025/08/15T14:00",
                ]
            }
        )
        out = to_date_column(df, "d")
        assert all(v == date(2025, 8, 15) for v in out["d"])

    def test_empty_becomes_none(self) -> None:
        df = pd.DataFrame({"d": ["", None]})
        out = to_date_column(df, "d")
        assert out["d"].iloc[0] is None
        assert out["d"].iloc[1] is None

    def test_result_col(self) -> None:
        df = pd.DataFrame({"d": ["2025-08-15"]})
        out = to_date_column(df, "d", result_col="d_date")
        assert out["d_date"].iloc[0] == date(2025, 8, 15)
        assert out["d"].dtype == object

    def test_missing_column(self) -> None:
        with pytest.raises(KeyError, match="欄位不存在"):
            to_date_column(pd.DataFrame({"a": [1]}), "d")

    def test_errors_raise(self) -> None:
        df = pd.DataFrame({"d": ["not-a-date"]})
        with pytest.raises(ValueError, match="無法解析為日期"):
            to_date_column(df, "d", errors="raise")

    def test_errors_coerce(self) -> None:
        df = pd.DataFrame({"d": ["2025-08-15", "bad"]})
        out = to_date_column(df, "d", errors="coerce")
        assert out["d"].iloc[0] == date(2025, 8, 15)
        assert out["d"].iloc[1] is None

    def test_as_string_true(self) -> None:
        df = pd.DataFrame({"d": ["2025/08/15", ""]})
        out = to_date_column(df, "d", as_string=True)
        assert out["d"].iloc[0] == "2025-08-15"
        assert out["d"].iloc[1] is None

    def test_as_string_false_keeps_date(self) -> None:
        df = pd.DataFrame({"d": ["2025-08-15"]})
        out = to_date_column(df, "d", as_string=False)
        assert out["d"].iloc[0] == date(2025, 8, 15)


class TestToTimeColumn:
    def test_mixed_formats(self) -> None:
        df = pd.DataFrame({"t": ["14:00:15", "14:00", "140015"]})
        out = to_time_column(df, "t")
        assert out["t"].iloc[0] == time(14, 0, 15)
        assert out["t"].iloc[1] == time(14, 0)
        assert out["t"].iloc[2] == time(14, 0, 15)

    def test_from_datetime_string(self) -> None:
        df = pd.DataFrame(
            {
                "t": [
                    "2025-08-15 14:00:15",
                    "2025-08-15T14:00:15",
                    "2025/08/15T14:00",
                ]
            }
        )
        out = to_time_column(df, "t")
        assert out["t"].iloc[0] == time(14, 0, 15)
        assert out["t"].iloc[1] == time(14, 0, 15)
        assert out["t"].iloc[2] == time(14, 0)

    def test_empty_becomes_none(self) -> None:
        df = pd.DataFrame({"t": [""]})
        out = to_time_column(df, "t")
        assert out["t"].iloc[0] is None

    def test_errors_raise(self) -> None:
        df = pd.DataFrame({"t": ["14:00:15", "bad"]})
        with pytest.raises(ValueError, match="無法解析為時間"):
            to_time_column(df, "t", errors="raise")

    def test_errors_coerce(self) -> None:
        df = pd.DataFrame({"t": ["14:00:15", "bad"]})
        out = to_time_column(df, "t", errors="coerce")
        assert out["t"].iloc[0] == time(14, 0, 15)
        assert out["t"].iloc[1] is None

    def test_2359_rolls_to_midnight(self) -> None:
        df = pd.DataFrame(
            {"t": ["23:59", "23:59:00", "235900", "23:59:01", "23:59:30", "23:59:59", "14:00"]}
        )
        out = to_time_column(df, "t")
        assert out["t"].iloc[0] == time(0, 0, 0)
        assert out["t"].iloc[1] == time(0, 0, 0)
        assert out["t"].iloc[2] == time(0, 0, 0)
        assert out["t"].iloc[3] == time(0, 0, 0)
        assert out["t"].iloc[4] == time(0, 0, 0)
        assert out["t"].iloc[5] == time(0, 0, 0)
        assert out["t"].iloc[6] == time(14, 0)

    def test_2359_from_datetime_string(self) -> None:
        df = pd.DataFrame({"t": ["2025-08-15 23:59", "2025-08-15T23:59:00"]})
        out = to_time_column(df, "t")
        assert out["t"].iloc[0] == time(0, 0, 0)
        assert out["t"].iloc[1] == time(0, 0, 0)

    def test_as_string_true(self) -> None:
        df = pd.DataFrame({"t": ["14:00:15", "23:59", ""]})
        out = to_time_column(df, "t", as_string=True)
        assert out["t"].iloc[0] == "14:00:15"
        assert out["t"].iloc[1] == "00:00:00"
        assert out["t"].iloc[2] is None

    def test_as_string_false_keeps_time(self) -> None:
        df = pd.DataFrame({"t": ["14:00:15"]})
        out = to_time_column(df, "t", as_string=False)
        assert out["t"].iloc[0] == time(14, 0, 15)


class TestToDatetimeColumn:
    def test_mixed_formats(self) -> None:
        df = pd.DataFrame(
            {
                "ts": [
                    "2025/08/15 14:00:15",
                    "2025/8/15 14:00:15",
                    "2025-08-15 14:00:15",
                    "2025-8-15 14:00:15",
                    "2025/08/15T14:00:15",
                    "2025-08-15T14:00:15",
                    "20250815140015",
                ]
            }
        )
        out = to_datetime_column(df, "ts")
        assert pd.api.types.is_datetime64_any_dtype(out["ts"])
        assert (out["ts"] == pd.Timestamp("2025-08-15 14:00:15")).all()
        assert df["ts"].dtype == object

    def test_iso_t_and_minute_only(self) -> None:
        df = pd.DataFrame(
            {
                "ts": [
                    "2025-08-15T14:00",
                    "2025/08/15T14:00",
                    "2025-08-15 14:00",
                    "2025/08/15 14:00",
                ]
            }
        )
        out = to_datetime_column(df, "ts")
        assert (out["ts"] == pd.Timestamp("2025-08-15 14:00:00")).all()

    def test_date_only_fills_midnight(self) -> None:
        df = pd.DataFrame({"ts": ["2025-08-15"]})
        out = to_datetime_column(df, "ts")
        assert out["ts"].iloc[0] == pd.Timestamp("2025-08-15 00:00:00")

    def test_already_timestamp(self) -> None:
        src = pd.Timestamp("2025-08-15 14:00:15")
        df = pd.DataFrame({"ts": [src]})
        out = to_datetime_column(df, "ts")
        assert out["ts"].iloc[0] == src

    def test_python_datetime(self) -> None:
        src = datetime(2025, 8, 15, 14, 0, 15)
        df = pd.DataFrame({"ts": [src]})
        out = to_datetime_column(df, "ts")
        assert out["ts"].iloc[0] == pd.Timestamp(src)

    def test_empty_becomes_nat(self) -> None:
        df = pd.DataFrame({"ts": ["", None]})
        out = to_datetime_column(df, "ts")
        assert pd.isna(out["ts"].iloc[0])
        assert pd.isna(out["ts"].iloc[1])

    def test_float_like_compact_string(self) -> None:
        df = pd.DataFrame({"ts": ["20250815140015.0"]})
        out = to_datetime_column(df, "ts")
        assert out["ts"].iloc[0] == pd.Timestamp("2025-08-15 14:00:15")

    def test_result_col(self) -> None:
        df = pd.DataFrame({"ts": ["2025-08-15 14:00:15"]})
        out = to_datetime_column(df, "ts", result_col="ts_dt")
        assert out["ts_dt"].iloc[0] == pd.Timestamp("2025-08-15 14:00:15")

    def test_invalid_errors_mode(self) -> None:
        df = pd.DataFrame({"ts": ["2025-08-15 14:00:15"]})
        with pytest.raises(ValueError, match="errors"):
            to_datetime_column(df, "ts", errors="ignore")  # type: ignore[arg-type]

    def test_errors_raise_on_bad_value(self) -> None:
        df = pd.DataFrame({"ts": ["2025-08-15 14:00:15", "bad"]})
        with pytest.raises(ValueError, match="無法解析"):
            to_datetime_column(df, "ts", errors="raise")

    def test_errors_coerce_on_bad_value(self) -> None:
        df = pd.DataFrame({"ts": ["2025-08-15 14:00:15", "bad"]})
        out = to_datetime_column(df, "ts", errors="coerce")
        assert out["ts"].iloc[0] == pd.Timestamp("2025-08-15 14:00:15")
        assert pd.isna(out["ts"].iloc[1])

    def test_2359_rolls_to_next_day(self) -> None:
        df = pd.DataFrame(
            {
                "ts": [
                    "2025-08-15 23:59",
                    "2025-08-15 23:59:00",
                    "2025/08/15T23:59",
                    "2025-08-15T23:59:00",
                    "20250815235900",
                    "2025-08-15 23:59:01",
                    "2025-08-15 23:59:30",
                    "2025-08-15 14:00:15",
                    pd.Timestamp("2025-08-15 23:59:00"),
                ]
            }
        )
        out = to_datetime_column(df, "ts")
        assert out["ts"].iloc[0] == pd.Timestamp("2025-08-16 00:00:00")
        assert out["ts"].iloc[1] == pd.Timestamp("2025-08-16 00:00:00")
        assert out["ts"].iloc[2] == pd.Timestamp("2025-08-16 00:00:00")
        assert out["ts"].iloc[3] == pd.Timestamp("2025-08-16 00:00:00")
        assert out["ts"].iloc[4] == pd.Timestamp("2025-08-16 00:00:00")
        assert out["ts"].iloc[5] == pd.Timestamp("2025-08-16 00:00:00")
        assert out["ts"].iloc[6] == pd.Timestamp("2025-08-16 00:00:00")
        assert out["ts"].iloc[7] == pd.Timestamp("2025-08-15 14:00:15")
        assert out["ts"].iloc[8] == pd.Timestamp("2025-08-16 00:00:00")

    def test_as_string_true(self) -> None:
        df = pd.DataFrame(
            {"ts": ["2025-08-15 14:00:15", "2025-08-15 23:59:01", ""]}
        )
        out = to_datetime_column(df, "ts", as_string=True)
        assert out["ts"].iloc[0] == "2025-08-15 14:00:15"
        assert out["ts"].iloc[1] == "2025-08-16 00:00:00"
        assert out["ts"].iloc[2] is None
        assert out["ts"].dtype == object

    def test_as_string_false_keeps_datetime(self) -> None:
        df = pd.DataFrame({"ts": ["2025-08-15 14:00:15"]})
        out = to_datetime_column(df, "ts", as_string=False)
        assert out["ts"].iloc[0] == pd.Timestamp("2025-08-15 14:00:15")
        assert pd.api.types.is_datetime64_any_dtype(out["ts"])
