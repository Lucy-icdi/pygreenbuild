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
from pygreenbuild.transform.transform_time import (
    _parse_date_value,
    _parse_datetime_value,
    _parse_time_value,
)


class TestParseDateValue:
    @pytest.mark.parametrize(
        "raw",
        [
            "2025/08/15",
            "2025/8/15",
            "2025-08-15",
            "2025-8-15",
            "20250815",
        ],
    )
    def test_supported_formats(self, raw: str) -> None:
        assert _parse_date_value(raw, errors="raise") == date(2025, 8, 15)

    def test_from_datetime_string(self) -> None:
        assert _parse_date_value(
            "2025-08-15 14:00:15", errors="raise"
        ) == date(2025, 8, 15)
        assert _parse_date_value(
            "2025-08-15T14:00:15", errors="raise"
        ) == date(2025, 8, 15)
        assert _parse_date_value(
            "2025/08/15T14:00", errors="raise"
        ) == date(2025, 8, 15)

    def test_empty_becomes_none(self) -> None:
        assert _parse_date_value("", errors="raise") is None
        assert _parse_date_value(None, errors="raise") is None

    def test_invalid_raise(self) -> None:
        with pytest.raises(ValueError, match="無法解析為日期"):
            _parse_date_value("not-a-date", errors="raise")

    def test_invalid_coerce(self) -> None:
        assert _parse_date_value("not-a-date", errors="coerce") is None


class TestParseTimeValue:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("14:00:15", time(14, 0, 15)),
            ("14:00", time(14, 0)),
            ("140015", time(14, 0, 15)),
        ],
    )
    def test_supported_formats(self, raw: str, expected: time) -> None:
        assert _parse_time_value(raw, errors="raise") == expected

    def test_from_datetime_string(self) -> None:
        assert _parse_time_value(
            "2025-08-15 14:00:15", errors="raise"
        ) == time(14, 0, 15)
        assert _parse_time_value(
            "2025-08-15T14:00:15", errors="raise"
        ) == time(14, 0, 15)
        assert _parse_time_value(
            "2025/08/15T14:00", errors="raise"
        ) == time(14, 0)

    def test_empty_becomes_none(self) -> None:
        assert _parse_time_value("", errors="raise") is None

    def test_invalid_raise(self) -> None:
        with pytest.raises(ValueError, match="無法解析為時間"):
            _parse_time_value("not-a-time", errors="raise")

    def test_invalid_coerce(self) -> None:
        assert _parse_time_value("not-a-time", errors="coerce") is None


class TestParseDatetimeValue:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("2025/08/15 14:00:15", "2025-08-15 14:00:15"),
            ("2025/8/15 14:00:15", "2025-08-15 14:00:15"),
            ("2025-08-15 14:00:15", "2025-08-15 14:00:15"),
            ("2025-8-15 14:00:15", "2025-08-15 14:00:15"),
            ("2025/08/15T14:00:15", "2025-08-15 14:00:15"),
            ("2025-08-15T14:00:15", "2025-08-15 14:00:15"),
            ("2025/08/15T14:00", "2025-08-15 14:00:00"),
            ("2025-08-15T14:00", "2025-08-15 14:00:00"),
            ("2025/08/15 14:00", "2025-08-15 14:00:00"),
            ("2025-08-15 14:00", "2025-08-15 14:00:00"),
            ("20250815140015", "2025-08-15 14:00:15"),
        ],
    )
    def test_supported_formats(self, raw: str, expected: str) -> None:
        ts = _parse_datetime_value(raw, errors="raise")
        assert ts == pd.Timestamp(expected)

    def test_date_only_fills_midnight(self) -> None:
        ts = _parse_datetime_value("2025-08-15", errors="raise")
        assert ts == pd.Timestamp("2025-08-15 00:00:00")

    def test_already_timestamp(self) -> None:
        src = pd.Timestamp("2025-08-15 14:00:15")
        assert _parse_datetime_value(src, errors="raise") == src

    def test_python_datetime(self) -> None:
        src = datetime(2025, 8, 15, 14, 0, 15)
        assert _parse_datetime_value(src, errors="raise") == pd.Timestamp(src)

    def test_empty_becomes_nat(self) -> None:
        assert pd.isna(_parse_datetime_value("", errors="raise"))
        assert pd.isna(_parse_datetime_value(None, errors="raise"))

    def test_float_like_compact_string(self) -> None:
        ts = _parse_datetime_value("20250815140015.0", errors="raise")
        assert ts == pd.Timestamp("2025-08-15 14:00:15")

    def test_invalid_raise(self) -> None:
        with pytest.raises(ValueError, match="無法解析為日期時間"):
            _parse_datetime_value("not-a-date", errors="raise")

    def test_invalid_coerce(self) -> None:
        assert pd.isna(_parse_datetime_value("not-a-date", errors="coerce"))


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

    def test_result_col(self) -> None:
        df = pd.DataFrame({"d": ["2025-08-15"]})
        out = to_date_column(df, "d", result_col="d_date")
        assert out["d_date"].iloc[0] == date(2025, 8, 15)
        assert out["d"].dtype == object

    def test_missing_column(self) -> None:
        with pytest.raises(KeyError, match="欄位不存在"):
            to_date_column(pd.DataFrame({"a": [1]}), "d")

    def test_errors_coerce(self) -> None:
        df = pd.DataFrame({"d": ["2025-08-15", "bad"]})
        out = to_date_column(df, "d", errors="coerce")
        assert out["d"].iloc[0] == date(2025, 8, 15)
        assert out["d"].iloc[1] is None


class TestToTimeColumn:
    def test_mixed_formats(self) -> None:
        df = pd.DataFrame({"t": ["14:00:15", "14:00", "140015"]})
        out = to_time_column(df, "t")
        assert out["t"].iloc[0] == time(14, 0, 15)
        assert out["t"].iloc[1] == time(14, 0)
        assert out["t"].iloc[2] == time(14, 0, 15)

    def test_errors_raise(self) -> None:
        df = pd.DataFrame({"t": ["14:00:15", "bad"]})
        with pytest.raises(ValueError, match="無法解析為時間"):
            to_time_column(df, "t", errors="raise")

    def test_errors_coerce(self) -> None:
        df = pd.DataFrame({"t": ["14:00:15", "bad"]})
        out = to_time_column(df, "t", errors="coerce")
        assert out["t"].iloc[0] == time(14, 0, 15)
        assert out["t"].iloc[1] is None


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
