"""transform.fill_time_gaps 單元測試。"""

from __future__ import annotations

import pandas as pd
import pytest

from pygreenbuild.transform import fill_time_gaps


def _hourly_base() -> pd.DataFrame:
    """建立缺 11:00 的小時資料。"""
    return pd.DataFrame(
        {
            "ts": pd.to_datetime(
                [
                    "2025-08-15 10:00:00",
                    "2025-08-15 12:00:00",
                    "2025-08-15 13:00:00",
                ]
            ),
            "value": [10.0, 12.0, 13.0],
            "label": ["a", "c", "d"],
        }
    )


class TestFillTimeGapsNa:
    def test_inserts_missing_hourly_rows_as_na(self) -> None:
        out = fill_time_gaps(_hourly_base(), "ts", "h", fill_method="na")
        assert len(out) == 4
        assert list(out["ts"]) == list(
            pd.to_datetime(
                [
                    "2025-08-15 10:00:00",
                    "2025-08-15 11:00:00",
                    "2025-08-15 12:00:00",
                    "2025-08-15 13:00:00",
                ]
            )
        )
        gap = out.loc[out["ts"] == pd.Timestamp("2025-08-15 11:00:00")].iloc[0]
        assert pd.isna(gap["value"])
        assert pd.isna(gap["label"])

    def test_does_not_mutate_input(self) -> None:
        df = _hourly_base()
        before = df.copy()
        fill_time_gaps(df, "ts", "h")
        pd.testing.assert_frame_equal(df, before)


class TestFillTimeGapsMethods:
    def test_ffill(self) -> None:
        out = fill_time_gaps(_hourly_base(), "ts", "h", fill_method="ffill")
        gap = out.loc[out["ts"] == pd.Timestamp("2025-08-15 11:00:00")].iloc[0]
        assert gap["value"] == 10.0
        assert gap["label"] == "a"

    def test_bfill(self) -> None:
        out = fill_time_gaps(_hourly_base(), "ts", "h", fill_method="bfill")
        gap = out.loc[out["ts"] == pd.Timestamp("2025-08-15 11:00:00")].iloc[0]
        assert gap["value"] == 12.0
        assert gap["label"] == "c"

    def test_neighbor_mean(self) -> None:
        out = fill_time_gaps(
            _hourly_base(), "ts", "h", fill_method="neighbor_mean"
        )
        gap = out.loc[out["ts"] == pd.Timestamp("2025-08-15 11:00:00")].iloc[0]
        assert gap["value"] == 11.0
        assert pd.isna(gap["label"])

    def test_constant(self) -> None:
        out = fill_time_gaps(
            _hourly_base(),
            "ts",
            "h",
            fill_method="constant",
            fill_value=-1,
        )
        gap = out.loc[out["ts"] == pd.Timestamp("2025-08-15 11:00:00")].iloc[0]
        assert gap["value"] == -1
        assert gap["label"] == -1

    def test_median(self) -> None:
        out = fill_time_gaps(_hourly_base(), "ts", "h", fill_method="median")
        gap = out.loc[out["ts"] == pd.Timestamp("2025-08-15 11:00:00")].iloc[0]
        # 原始數值 10, 12, 13 → 中位數 12
        assert gap["value"] == 12.0
        assert pd.isna(gap["label"])


class TestFillTimeGapsFreq:
    def test_three_minute_freq(self) -> None:
        df = pd.DataFrame(
            {
                "ts": pd.to_datetime(
                    [
                        "2025-08-15 10:00:00",
                        "2025-08-15 10:06:00",
                    ]
                ),
                "value": [1.0, 3.0],
            }
        )
        out = fill_time_gaps(df, "ts", "3min", fill_method="na")
        assert list(out["ts"]) == list(
            pd.to_datetime(
                [
                    "2025-08-15 10:00:00",
                    "2025-08-15 10:03:00",
                    "2025-08-15 10:06:00",
                ]
            )
        )
        assert pd.isna(out.loc[1, "value"])

    def test_five_minute_freq(self) -> None:
        df = pd.DataFrame(
            {
                "ts": pd.to_datetime(
                    [
                        "2025-08-15 10:00:00",
                        "2025-08-15 10:10:00",
                    ]
                ),
                "value": [1.0, 2.0],
            }
        )
        out = fill_time_gaps(df, "ts", "5min")
        assert len(out) == 3
        assert out.loc[1, "ts"] == pd.Timestamp("2025-08-15 10:05:00")


class TestFillTimeGapsErrors:
    def test_missing_column(self) -> None:
        with pytest.raises(KeyError, match="欄位不存在"):
            fill_time_gaps(_hourly_base(), "missing", "h")

    def test_empty_df(self) -> None:
        df = pd.DataFrame({"ts": pd.to_datetime([]), "value": pd.Series([], dtype=float)})
        with pytest.raises(ValueError, match="不可為空"):
            fill_time_gaps(df, "ts", "h")

    def test_invalid_fill_method(self) -> None:
        with pytest.raises(ValueError, match="fill_method"):
            fill_time_gaps(_hourly_base(), "ts", "h", fill_method="noop")  # type: ignore[arg-type]

    def test_constant_requires_fill_value(self) -> None:
        with pytest.raises(ValueError, match="fill_value"):
            fill_time_gaps(_hourly_base(), "ts", "h", fill_method="constant")

    def test_duplicate_timestamps(self) -> None:
        df = pd.DataFrame(
            {
                "ts": pd.to_datetime(
                    ["2025-08-15 10:00:00", "2025-08-15 10:00:00"]
                ),
                "value": [1.0, 2.0],
            }
        )
        with pytest.raises(ValueError, match="重複時間戳"):
            fill_time_gaps(df, "ts", "h")

    def test_nat_in_datetime(self) -> None:
        df = pd.DataFrame(
            {
                "ts": [pd.Timestamp("2025-08-15 10:00:00"), pd.NaT],
                "value": [1.0, 2.0],
            }
        )
        with pytest.raises(ValueError, match="空值"):
            fill_time_gaps(df, "ts", "h")

    def test_empty_freq(self) -> None:
        with pytest.raises(ValueError, match="freq"):
            fill_time_gaps(_hourly_base(), "ts", "")

    def test_not_dataframe(self) -> None:
        with pytest.raises(TypeError, match="DataFrame"):
            fill_time_gaps([1, 2, 3], "ts", "h")  # type: ignore[arg-type]
