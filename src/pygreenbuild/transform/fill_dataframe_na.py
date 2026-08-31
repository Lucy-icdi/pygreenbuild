"""對 pandas DataFrame 填補孤立 NA，回傳新的完整 DataFrame。"""

from __future__ import annotations

from typing import Any

import pandas as pd

from pygreenbuild.transform.fill_surrounded_na import (
    FillSurroundedMethod,
    _fill_surrounded_na,
)


def fill_dataframe_na(
    df: pd.DataFrame,
    *,
    range_col: str | None = None,
    range_start: Any = None,
    range_end: Any = None,
    exclude_cols: list[str] | None = None,
    fill_method: FillSurroundedMethod = "neighbor_mean",
    fill_value: object | None = None,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """填補 DataFrame 的孤立 NA，回傳**新的**完整表（不修改原表）。

    Parameters
    ----------
    df :
        輸入資料表；不會被修改（單位：不適用）。
    range_col / range_start / range_end :
        可選。只在此範圍內的列做填補；三者皆給或皆省略
        （單位：依欄位而定）。範圍外列原樣複製到新表。
    exclude_cols :
        不參與填補的欄位（單位：不適用）。``range_col`` 會自動排除。
    fill_method :
        填值策略（單位：不適用）：``"neighbor_mean"``、``"ffill"``、
        ``"bfill"``、``"constant"``。
    fill_value :
        ``fill_method="constant"`` 時使用（單位：依欄位而定）。
    columns :
        只填這些欄；``None`` 表示除排除欄外全部欄位（單位：不適用）。

    Returns
    -------
    pd.DataFrame
        已填補的新表（完整列／欄，與輸入同形狀）（單位：不適用）。

    Raises
    ------
    TypeError
        ``df`` 不是 DataFrame。
    ValueError
        範圍參數不完整，或沒有可填補欄位。
    KeyError
        指定欄位不存在。
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"df 須為 pandas.DataFrame，收到 {type(df)!r}")

    provided = [
        range_col is not None,
        range_start is not None,
        range_end is not None,
    ]
    if any(provided) and not all(provided):
        raise ValueError(
            "range_col、range_start、range_end 須同時指定，"
            "或全部省略以使用全部列"
        )

    out = df.copy()
    if out.empty:
        return out

    if range_col is not None:
        if range_col not in out.columns:
            raise KeyError(
                f"資料不含範圍欄位 {range_col!r}（實際欄位: {list(out.columns)}）"
            )
        mask = (out[range_col] >= range_start) & (out[range_col] <= range_end)
        work = out.loc[mask].sort_values(range_col, kind="mergesort")
    else:
        work = out

    if work.empty:
        return out

    excluded = list(exclude_cols or [])
    if range_col is not None:
        excluded.append(range_col)
    excluded = list(dict.fromkeys(excluded))

    filled, _n_filled = _fill_surrounded_na(
        work,
        fill_method=fill_method,
        fill_value=fill_value,
        columns=columns,
        exclude_cols=excluded or None,
    )

    changed = work.isna() & filled.notna()
    for col in excluded:
        if col in changed.columns:
            changed[col] = False

    for col in changed.columns:
        col_mask = changed[col]
        if bool(col_mask.any()):
            out.loc[col_mask.index[col_mask], col] = filled.loc[
                col_mask, col
            ].to_numpy()

    return out
