"""load.apply_filled_na 單元測試。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from pygreenbuild.load import apply_filled_na


def _seed_engine() -> Any:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    df = pd.DataFrame(
        {
            "DateTime": [2026070100, 2026070101, 2026070102],
            "temp": [20.0, None, 24.0],
            "hum": [50.0, 55.0, None],
        }
    )
    df.to_sql("c2c480", engine, index=False, if_exists="replace")
    return engine


def _sample_result() -> dict[str, Any]:
    return {
        "table_name": "c2c480",
        "key_cols": ["DateTime"],
        "records": [
            {"DateTime": 2026070101, "temp": 22.0},
            {"DateTime": 2026070102, "hum": 60.0},
        ],
    }


class TestApplyFilledNaExecute:
    def test_updates_mysql_like_rows(self) -> None:
        engine = _seed_engine()
        try:
            out = apply_filled_na(
                _sample_result(),
                engine=engine,
                sql_only=False,
            )
            with engine.connect() as conn:
                rows = (
                    conn.execute(
                        text(
                            "SELECT DateTime, temp, hum FROM c2c480 "
                            "ORDER BY DateTime"
                        )
                    )
                    .mappings()
                    .all()
                )
        finally:
            engine.dispose()

        assert out["n_statements"] == 2
        assert out["sql_only"] is False
        by_key = {r["DateTime"]: r for r in rows}
        assert by_key[2026070101]["temp"] == 22.0
        assert by_key[2026070102]["hum"] == 60.0

    def test_requires_connection_when_not_sql_only(self) -> None:
        with pytest.raises(ValueError, match="connection_str"):
            apply_filled_na(_sample_result(), sql_only=False)


class TestApplyFilledNaSqlOnly:
    def test_writes_sql_file(self, tmp_path: Path) -> None:
        path = tmp_path / "out.sql"
        out = apply_filled_na(
            _sample_result(),
            sql_only=True,
            sql_path=path,
        )
        assert out["sql_only"] is True
        assert out["n_rowcount"] is None
        assert out["n_statements"] == 2
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "UPDATE `c2c480` SET `temp` = 22" in content
        assert "WHERE `DateTime` = 2026070101" in content
        assert "UPDATE `c2c480` SET `hum` = 60" in content

    def test_empty_records(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.sql"
        out = apply_filled_na(
            {
                "table_name": "c2c480",
                "key_cols": ["DateTime"],
                "records": [],
            },
            sql_only=True,
            sql_path=path,
        )
        assert out["n_statements"] == 0
        assert path.exists()


class TestApplyFilledNaErrors:
    def test_missing_key_cols(self) -> None:
        with pytest.raises(ValueError, match="key_cols"):
            apply_filled_na(
                {"table_name": "c2c480", "key_cols": None, "records": []},
                sql_only=True,
            )

    def test_record_missing_key(self, tmp_path: Path) -> None:
        with pytest.raises(KeyError, match="key_cols"):
            apply_filled_na(
                {
                    "table_name": "c2c480",
                    "key_cols": ["DateTime"],
                    "records": [{"temp": 1.0}],
                },
                sql_only=True,
                sql_path=tmp_path / "x.sql",
            )
