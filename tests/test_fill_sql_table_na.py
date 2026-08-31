"""ingestion.ems_db.factory_db 單元測試。"""

from __future__ import annotations

from typing import Any

import pandas as pd
import pytest
from sqlalchemy import create_engine

from pygreenbuild.ingestion.ems_db import fill_sql_table_na


def _make_sqlite_engine_with_table() -> Any:
    """建立含示範資料的記憶體 SQLite engine。"""
    engine = create_engine("sqlite+pysqlite:///:memory:")
    df = pd.DataFrame(
        {
            "DateTime": [2026040100, 2026040101, 2026040102, 2026040103],
            "temp": [20.0, None, 24.0, 25.0],
            "hum": [50.0, 55.0, None, 65.0],
        }
    )
    df.to_sql("c2c480", engine, index=False, if_exists="replace")
    return engine


class TestFillSqlTableNa:
    def test_neighbor_mean_returns_dict_with_records(self) -> None:
        engine = _make_sqlite_engine_with_table()
        try:
            result = fill_sql_table_na(
                "sqlite+pysqlite:///:memory:",
                "c2c480",
                range_col="DateTime",
                range_start=2026040100,
                range_end=2026073123,
                fill_method="neighbor_mean",
                engine=engine,
            )
        finally:
            engine.dispose()

        assert result["table_name"] == "c2c480"
        assert result["range_col"] == "DateTime"
        assert result["n_rows"] == 4
        assert result["n_filled_cells"] == 2
        by_key = {r["DateTime"]: r for r in result["records"]}
        assert by_key[2026040101]["temp"] == 22.0
        assert by_key[2026040102]["hum"] == 60.0

    def test_read_entire_table_without_range(self) -> None:
        engine = _make_sqlite_engine_with_table()
        try:
            result = fill_sql_table_na(
                "unused",
                "c2c480",
                exclude_cols=["DateTime"],
                engine=engine,
            )
        finally:
            engine.dispose()

        assert result["range_col"] is None
        assert result["n_rows"] == 4
        assert result["n_filled_cells"] == 2

    def test_key_cols_returns_only_changed_slim_records(self) -> None:
        engine = _make_sqlite_engine_with_table()
        try:
            result = fill_sql_table_na(
                "unused",
                "c2c480",
                range_col="DateTime",
                range_start=2026040100,
                range_end=2026073123,
                exclude_cols=["DateTime"],
                key_cols=["DateTime"],
                engine=engine,
            )
        finally:
            engine.dispose()

        assert result["records"] == [
            {"DateTime": 2026040101, "temp": 22.0},
            {"DateTime": 2026040102, "hum": 60.0},
        ]

    def test_partial_range_args_raises(self) -> None:
        with pytest.raises(ValueError, match="同時指定"):
            fill_sql_table_na(
                "sqlite+pysqlite:///:memory:",
                "c2c480",
                range_col="DateTime",
            )

    def test_rejects_unsafe_table_name(self) -> None:
        with pytest.raises(ValueError, match="非法字元"):
            fill_sql_table_na(
                "sqlite+pysqlite:///:memory:",
                "c2c480; DROP TABLE x",
            )

    def test_rejects_unsafe_range_col(self) -> None:
        with pytest.raises(ValueError, match="非法字元"):
            fill_sql_table_na(
                "sqlite+pysqlite:///:memory:",
                "c2c480",
                range_col="DateTime; DROP TABLE x",
                range_start=1,
                range_end=2,
            )
