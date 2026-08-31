"""transform.fill_dataframe_na 單元測試。"""

from __future__ import annotations

import pandas as pd
import pytest

from pygreenbuild.transform import fill_dataframe_na


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "DateTime": [2026040100, 2026040101, 2026040102, 2026040103],
            "temp": [20.0, None, 24.0, 25.0],
            "hum": [50.0, 55.0, None, 65.0],
            "label": ["x", None, "z", "w"],
        }
    )


class TestFillDataframeNa:
    def test_returns_new_filled_dataframe(self) -> None:
        df = _sample_df()
        out = fill_dataframe_na(df, exclude_cols=["DateTime"])
        assert out is not df
        assert pd.isna(df.loc[1, "temp"])
        assert out.loc[1, "temp"] == 22.0
        assert out.loc[2, "hum"] == 60.0
        assert pd.isna(out.loc[1, "label"])
        assert len(out) == len(df)
        assert list(out.columns) == list(df.columns)

    def test_does_not_mutate_input(self) -> None:
        df = _sample_df()
        before = df.copy()
        fill_dataframe_na(df, exclude_cols=["DateTime"])
        pd.testing.assert_frame_equal(df, before)

    def test_range_only_affects_rows_in_range(self) -> None:
        df = _sample_df()
        out = fill_dataframe_na(
            df,
            range_col="DateTime",
            range_start=2026040100,
            range_end=2026040102,
            exclude_cols=["DateTime"],
        )
        assert out.loc[1, "temp"] == 22.0
        assert pd.isna(out.loc[2, "hum"])
        assert out.loc[3, "temp"] == 25.0
        assert pd.isna(df.loc[1, "temp"])

    def test_allows_column_names_that_are_not_sql_identifiers(self) -> None:
        df = pd.DataFrame(
            {
                "觀測時間": [1, 2, 3],
                "氣溫": [20.0, None, 24.0],
            }
        )
        out = fill_dataframe_na(df, exclude_cols=["觀測時間"])
        assert out.loc[1, "氣溫"] == 22.0

    def test_rounds_to_neighbor_decimal_places(self) -> None:
        df = pd.DataFrame({"v": [20.1, None, 20.2]})
        out = fill_dataframe_na(df)
        assert out.loc[1, "v"] == 20.2

    def test_preserves_two_decimal_places(self) -> None:
        df = pd.DataFrame({"v": [1.25, None, 1.35]})
        out = fill_dataframe_na(df)
        assert out.loc[1, "v"] == 1.30

    def test_ffill(self) -> None:
        out = fill_dataframe_na(
            _sample_df(), fill_method="ffill", exclude_cols=["DateTime"]
        )
        assert out.loc[1, "temp"] == 20.0
        assert out.loc[2, "hum"] == 55.0
        assert out.loc[1, "label"] == "x"

    def test_bfill(self) -> None:
        out = fill_dataframe_na(
            _sample_df(), fill_method="bfill", exclude_cols=["DateTime"]
        )
        assert out.loc[1, "temp"] == 24.0
        assert out.loc[2, "hum"] == 65.0
        assert out.loc[1, "label"] == "z"

    def test_constant(self) -> None:
        out = fill_dataframe_na(
            _sample_df(),
            fill_method="constant",
            fill_value=-999,
            exclude_cols=["DateTime"],
        )
        assert out.loc[1, "temp"] == -999
        assert out.loc[2, "hum"] == -999
        assert out.loc[1, "label"] == -999

    def test_skips_leading_and_trailing_na(self) -> None:
        df = pd.DataFrame({"v": [None, 1.0, None, 3.0, None]})
        out = fill_dataframe_na(df, fill_method="neighbor_mean")
        assert out.loc[2, "v"] == 2.0
        assert pd.isna(out.loc[0, "v"])
        assert pd.isna(out.loc[4, "v"])

    def test_skips_consecutive_na(self) -> None:
        df = pd.DataFrame({"v": [1.0, None, None, 4.0]})
        out = fill_dataframe_na(df, fill_method="ffill")
        assert pd.isna(out.loc[1, "v"])
        assert pd.isna(out.loc[2, "v"])

    def test_columns_filter(self) -> None:
        out = fill_dataframe_na(
            _sample_df(),
            fill_method="neighbor_mean",
            columns=["temp"],
            exclude_cols=["DateTime"],
        )
        assert out.loc[1, "temp"] == 22.0
        assert pd.isna(out.loc[2, "hum"])

    def test_partial_range_args_raises(self) -> None:
        with pytest.raises(ValueError, match="同時指定"):
            fill_dataframe_na(_sample_df(), range_col="DateTime")

    def test_bad_df_type(self) -> None:
        with pytest.raises(TypeError, match="DataFrame"):
            fill_dataframe_na([1, 2, 3])  # type: ignore[arg-type]

    def test_bad_method(self) -> None:
        with pytest.raises(ValueError, match="fill_method"):
            fill_dataframe_na(_sample_df(), fill_method="median")  # type: ignore[arg-type]

    def test_constant_requires_value(self) -> None:
        with pytest.raises(ValueError, match="fill_value"):
            fill_dataframe_na(_sample_df(), fill_method="constant")

    def test_missing_column(self) -> None:
        with pytest.raises(KeyError, match="不存在"):
            fill_dataframe_na(_sample_df(), columns=["nope"])

    def test_empty_target_columns(self) -> None:
        df = pd.DataFrame({"DateTime": [1, 2, 3]})
        with pytest.raises(ValueError, match="沒有可填補"):
            fill_dataframe_na(df, exclude_cols=["DateTime"])
