"""依指定頻率補齊時間序列中缺失的列，並以選定策略填值。"""

from __future__ import annotations

from typing import Literal

import pandas as pd

FillMethod = Literal[
    "na",
    "ffill",
    "bfill",
    "neighbor_mean",
    "constant",
    "median",
]

_ALLOWED_FILL_METHODS: frozenset[str] = frozenset(
    {"na", "ffill", "bfill", "neighbor_mean", "constant", "median"}
)


def _validate_inputs(
    df: pd.DataFrame,
    datetime_col: str,
    freq: str,
    fill_method: str,
    fill_value: object | None,
) -> None:
    """驗證 ``fill_time_gaps`` 的輸入參數。"""
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"df 須為 pandas.DataFrame，收到 {type(df)!r}")
    if datetime_col not in df.columns:
        raise KeyError(f"欄位不存在: {datetime_col!r}")
    if not isinstance(freq, str) or not freq.strip():
        raise ValueError(f"freq 須為非空字串，收到 {freq!r}")
    if fill_method not in _ALLOWED_FILL_METHODS:
        raise ValueError(
            "fill_method 須為 "
            f"{sorted(_ALLOWED_FILL_METHODS)} 之一，收到 {fill_method!r}"
        )
    if fill_method == "constant" and fill_value is None:
        raise ValueError("fill_method='constant' 時必須提供 fill_value")
    if df.empty:
        raise ValueError("df 不可為空")


def _prepare_datetime_series(
    df: pd.DataFrame, datetime_col: str
) -> pd.Series:
    """將日期時間欄轉為 ``datetime64``，並檢查空值與重複。"""
    series = pd.to_datetime(df[datetime_col], errors="coerce")
    if series.isna().any():
        bad_idx = series[series.isna()].index.tolist()
        raise ValueError(
            f"日期時間欄 {datetime_col!r} 含無法解析或空值，"
            f"列索引: {bad_idx}"
        )
    if series.duplicated().any():
        dup_vals = series[series.duplicated()].unique().tolist()
        raise ValueError(
            f"日期時間欄 {datetime_col!r} 含重複時間戳: {dup_vals}"
        )
    return series


def _apply_neighbor_mean(frame: pd.DataFrame) -> pd.DataFrame:
    """對數值欄以「前後筆平均值」填補缺失；非數值欄維持 ``NA``。"""
    out = frame.copy()
    numeric_cols = out.select_dtypes(include="number").columns
    for col in numeric_cols:
        s = out[col]
        prev_vals = s.shift(1)
        next_vals = s.shift(-1)
        mask = s.isna() & prev_vals.notna() & next_vals.notna()
        out.loc[mask, col] = (prev_vals[mask] + next_vals[mask]) / 2.0
    return out


def _apply_fill(
    frame: pd.DataFrame,
    *,
    fill_method: FillMethod,
    fill_value: object | None,
    original: pd.DataFrame,
) -> pd.DataFrame:
    """依策略填補非日期時間欄的缺失值。"""
    if fill_method == "na":
        return frame
    if fill_method == "ffill":
        return frame.ffill()
    if fill_method == "bfill":
        return frame.bfill()
    if fill_method == "constant":
        return frame.fillna(fill_value)
    if fill_method == "median":
        out = frame.copy()
        numeric_cols = out.select_dtypes(include="number").columns
        for col in numeric_cols:
            med = original[col].median(skipna=True)
            if pd.notna(med):
                out[col] = out[col].fillna(med)
        return out
    # neighbor_mean
    return _apply_neighbor_mean(frame)


def fill_time_gaps(
    df: pd.DataFrame,
    datetime_col: str,
    freq: str,
    *,
    fill_method: FillMethod = "na",
    fill_value: object | None = None,
) -> pd.DataFrame:
    """依手動指定頻率補齊連續時間軸中缺失的列。

    以 ``datetime_col`` 的最小與最大時間為邊界，用 ``freq`` 產生完整時間軸；
    缺漏時間點會新增一列，其餘欄位依 ``fill_method`` 填值。

    Parameters
    ----------
    df :
        輸入資料表（單位：不適用）。
    datetime_col :
        日期時間欄位名稱（單位：不適用）。
    freq :
        時間頻率字串，例如 ``"h"``、``"3min"``、``"5min"``（單位：不適用）。
        須為 pandas 可解析的 offset alias。
    fill_method :
        新增列（及其他既有 ``NA``）的填值策略（單位：不適用）：

        - ``"na"``：維持 ``NA``（預設）
        - ``"ffill"``：以前一筆代替
        - ``"bfill"``：以後一筆代替
        - ``"neighbor_mean"``：前後筆平均值（僅數值欄；缺任一邊則維持 ``NA``）
        - ``"constant"``：以 ``fill_value`` 代替
        - ``"median"``：以該欄原始資料的中位數代替（僅數值欄）
    fill_value :
        ``fill_method="constant"`` 時使用的指定值（單位：依欄位而定）；
        其他策略可省略。

    Returns
    -------
    pd.DataFrame
        補齊時間軸後的新資料表，依 ``datetime_col`` 升冪排序；不修改原表
        （單位：不適用）。

    Raises
    ------
    TypeError
        ``df`` 不是 ``pandas.DataFrame``。
    KeyError
        ``datetime_col`` 不存在於 ``df``。
    ValueError
        ``freq``／``fill_method`` 非法、``constant`` 未提供 ``fill_value``、
        ``df`` 為空、日期時間含空值／無法解析、或有重複時間戳。
    """
    _validate_inputs(df, datetime_col, freq, fill_method, fill_value)

    work = df.copy()
    work[datetime_col] = _prepare_datetime_series(work, datetime_col)
    work = work.sort_values(datetime_col).reset_index(drop=True)

    start = work[datetime_col].iloc[0]
    end = work[datetime_col].iloc[-1]
    try:
        full_index = pd.date_range(start=start, end=end, freq=freq)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"無法解析 freq={freq!r}: {exc}") from exc

    if len(full_index) == 0:
        raise ValueError(
            f"以 freq={freq!r} 自 {start} 至 {end} 無法產生任何時間點"
        )

    # 若既有時間點不在完整軸上（例如頻率與資料不對齊），仍保留並與完整軸聯集
    union_index = full_index.union(pd.DatetimeIndex(work[datetime_col]))
    value_cols = [c for c in work.columns if c != datetime_col]
    indexed = work.set_index(datetime_col)
    aligned = indexed.reindex(union_index)
    filled = _apply_fill(
        aligned,
        fill_method=fill_method,
        fill_value=fill_value,
        original=indexed,
    )
    filled.index.name = datetime_col
    out = filled.reset_index()
    ordered_cols = [datetime_col] + value_cols
    return out[ordered_cols].reset_index(drop=True)
