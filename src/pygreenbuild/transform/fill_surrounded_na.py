"""填補「上下皆有值、本身為 NA」的儲存格。"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

import pandas as pd

FillSurroundedMethod = Literal[
    "neighbor_mean",
    "ffill",
    "bfill",
    "constant",
]

_ALLOWED_METHODS: frozenset[str] = frozenset(
    {"neighbor_mean", "ffill", "bfill", "constant"}
)


def _validate_inputs(
    df: pd.DataFrame,
    *,
    fill_method: str,
    fill_value: object | None,
    columns: list[str] | None,
    exclude_cols: list[str] | None,
) -> list[str]:
    """驗證輸入並回傳實際要填補的欄位清單。"""
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"df 須為 pandas.DataFrame，收到 {type(df)!r}")
    if fill_method not in _ALLOWED_METHODS:
        raise ValueError(
            "fill_method 須為 "
            f"{sorted(_ALLOWED_METHODS)} 之一，收到 {fill_method!r}"
        )
    if fill_method == "constant" and fill_value is None:
        raise ValueError("fill_method='constant' 時必須提供 fill_value")

    exclude = set(exclude_cols or [])
    if columns is not None:
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise KeyError(f"欄位不存在: {missing}")
        target = [c for c in columns if c not in exclude]
    else:
        target = [c for c in df.columns if c not in exclude]

    if not target:
        raise ValueError("沒有可填補的欄位（columns 與 exclude_cols 篩選後為空）")
    return target


def _surrounded_mask(series: pd.Series) -> pd.Series:
    """標記「本身 NA，且上一列與下一列皆非 NA」的位置。"""
    prev_ok = series.shift(1).notna()
    next_ok = series.shift(-1).notna()
    return series.isna() & prev_ok & next_ok


def _decimal_places(value: object) -> int:
    """由數值字面推斷小數位數（不含多餘浮點雜訊）。"""
    d = Decimal(str(value))
    exp = d.as_tuple().exponent
    if isinstance(exp, int) and exp < 0:
        return -exp
    return 0


def _neighbor_mean_value(prev: object, next_: object) -> float:
    """上下平均，並四捨五入至不超過兩側小數位數的最大值。"""
    p = Decimal(str(prev))
    n = Decimal(str(next_))
    mean = (p + n) / Decimal(2)
    ndigits = max(_decimal_places(prev), _decimal_places(next_))
    quant = Decimal(1).scaleb(-ndigits) if ndigits > 0 else Decimal(1)
    return float(mean.quantize(quant, rounding=ROUND_HALF_UP))


def _fill_one_column(
    series: pd.Series,
    *,
    fill_method: FillSurroundedMethod,
    fill_value: object | None,
) -> tuple[pd.Series, int]:
    """依策略填補單一欄位，回傳（新序列, 填補筆數）。"""
    mask = _surrounded_mask(series)
    n_filled = int(mask.sum())
    if n_filled == 0:
        return series.copy(), 0

    out = series.copy()
    if fill_method == "neighbor_mean":
        if not pd.api.types.is_numeric_dtype(series):
            return out, 0
        prev_vals = series.shift(1)
        next_vals = series.shift(-1)
        filled_vals = [
            _neighbor_mean_value(prev_vals.loc[i], next_vals.loc[i])
            for i in series.index[mask]
        ]
        out.loc[mask] = filled_vals
        return out, n_filled
    if fill_method == "ffill":
        out.loc[mask] = series.shift(1)[mask]
        return out, n_filled
    if fill_method == "bfill":
        out.loc[mask] = series.shift(-1)[mask]
        return out, n_filled
    # constant
    out.loc[mask] = fill_value
    return out, n_filled


def _fill_surrounded_na(
    df: pd.DataFrame,
    *,
    fill_method: FillSurroundedMethod = "neighbor_mean",
    fill_value: object | None = None,
    columns: list[str] | None = None,
    exclude_cols: list[str] | None = None,
) -> tuple[pd.DataFrame, int]:
    """（內部）填補上下皆有資料、本身為 NA 的儲存格。

    僅處理「緊鄰上一列與下一列皆非 NA」的孤立缺口；開頭／結尾連續 NA、
    或連續多個 NA 中間格（鄰居仍為 NA）不會被填補。

    Parameters
    ----------
    df :
        輸入資料表；呼叫端應先依時間（或其他順序欄）排好序
        （單位：不適用）。
    fill_method :
        填值策略（單位：不適用）：

        - ``"neighbor_mean"``：上下平均值（僅數值欄；非數值欄略過）。
          結果會四捨五入至不超過上下兩筆小數位數的較大者，
          避免平均後多出額外小數位。
        - ``"ffill"``：以上一列（向下填補）
        - ``"bfill"``：以下一列（向上填補）
        - ``"constant"``：以 ``fill_value`` 填補
    fill_value :
        ``fill_method="constant"`` 時使用的指定值（單位：依欄位而定）。
    columns :
        僅填補這些欄位；``None`` 表示除 ``exclude_cols`` 外全部欄位
        （單位：不適用）。
    exclude_cols :
        永不填補的欄位（例如主鍵、時間索引欄）（單位：不適用）。

    Returns
    -------
    tuple[pd.DataFrame, int]
        ``(填補後的新表, 實際填補的儲存格數)``；不修改原表
        （單位：不適用）。

    Raises
    ------
    TypeError
        ``df`` 不是 ``pandas.DataFrame``。
    KeyError
        ``columns`` 中有不存在的欄位。
    ValueError
        ``fill_method`` 非法、``constant`` 未提供 ``fill_value``、
        或可填補欄位為空。
    """
    target_cols = _validate_inputs(
        df,
        fill_method=fill_method,
        fill_value=fill_value,
        columns=columns,
        exclude_cols=exclude_cols,
    )

    out = df.copy()
    total_filled = 0
    for col in target_cols:
        filled_series, n = _fill_one_column(
            out[col],
            fill_method=fill_method,
            fill_value=fill_value,
        )
        if n > 0:
            out[col] = filled_series
            total_filled += n
    return out, total_filled
