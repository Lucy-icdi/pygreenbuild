"""孤立 NA 填補結果組裝（供 ``fill_sql_table_na`` 使用）。"""

from __future__ import annotations

from typing import Any

import pandas as pd

from pygreenbuild.transform.fill_surrounded_na import (
    FillSurroundedMethod,
    _fill_surrounded_na,
)


def _to_python(value: Any) -> Any:
    """將 pandas／numpy 純量轉成 Python 原生型別；空值為 ``None``。"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item") and not isinstance(value, (bytes, str)):
        try:
            return value.item()
        except (ValueError, AttributeError):
            pass
    return value


def records_for_db(df: pd.DataFrame) -> list[dict[str, Any]]:
    """將 DataFrame 轉成 list[dict]，空值一律為 ``None``。"""
    cleaned = df.where(pd.notna(df), None)
    return [
        {k: _to_python(v) for k, v in row.items()}
        for row in cleaned.to_dict(orient="records")
    ]


def slim_filled_records(
    original: pd.DataFrame,
    filled: pd.DataFrame,
    *,
    key_cols: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    """只保留有填補的列；每列僅含 ``key_cols`` + 該列實際被填補的欄。"""
    missing = [c for c in key_cols if c not in filled.columns]
    if missing:
        raise KeyError(f"key_cols 欄位不存在: {missing}")

    fill_flags = original.isna() & filled.notna()
    filled_cols = [c for c in fill_flags.columns if bool(fill_flags[c].any())]
    row_indices = filled.index[fill_flags.any(axis=1)]

    records: list[dict[str, Any]] = []
    for idx in row_indices:
        row_filled = [c for c in fill_flags.columns if bool(fill_flags.at[idx, c])]
        cols = list(dict.fromkeys([*key_cols, *row_filled]))
        row = filled.loc[idx, cols]
        records.append({col: _to_python(row[col]) for col in cols})
    return records, filled_cols


def build_filled_na_result(
    df: pd.DataFrame,
    *,
    table_name: str,
    range_col: str | None,
    range_start: Any,
    range_end: Any,
    exclude_cols: list[str] | None,
    key_cols: list[str] | None,
    fill_method: FillSurroundedMethod,
    fill_value: object | None,
    columns: list[str] | None,
) -> dict[str, Any]:
    """對 DataFrame 填補並組裝與 ``fill_sql_table_na`` 相同結構的 dict。"""
    empty_result: dict[str, Any] = {
        "table_name": table_name,
        "range_col": range_col,
        "range_start": range_start if range_col is not None else None,
        "range_end": range_end if range_col is not None else None,
        "exclude_cols": list(exclude_cols or []),
        "key_cols": list(key_cols) if key_cols is not None else None,
        "filled_cols": [],
        "fill_method": fill_method,
        "n_rows": 0,
        "n_filled_cells": 0,
        "records": [],
    }
    if df.empty:
        return empty_result

    excluded = list(exclude_cols or [])
    if range_col is not None:
        excluded.append(range_col)
    if key_cols is not None:
        excluded.extend(key_cols)
    excluded = list(dict.fromkeys(excluded))

    filled, n_filled = _fill_surrounded_na(
        df,
        fill_method=fill_method,
        fill_value=fill_value,
        columns=columns,
        exclude_cols=excluded or None,
    )

    fill_flags = df.isna() & filled.notna()
    for col in excluded:
        if col in fill_flags.columns:
            fill_flags[col] = False
    filled_cols = [c for c in fill_flags.columns if bool(fill_flags[c].any())]

    if key_cols is not None:
        records, filled_cols = slim_filled_records(df, filled, key_cols=key_cols)
    else:
        records = records_for_db(filled)

    return {
        "table_name": table_name,
        "range_col": range_col,
        "range_start": range_start if range_col is not None else None,
        "range_end": range_end if range_col is not None else None,
        "exclude_cols": list(exclude_cols or []),
        "key_cols": list(key_cols) if key_cols is not None else None,
        "filled_cols": filled_cols,
        "fill_method": fill_method,
        "n_rows": int(len(df)),
        "n_filled_cells": int(n_filled),
        "records": records,
    }
