"""時間相關欄位轉換：純日期、純時間、日期時間。"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Callable, Literal, TypeVar

import pandas as pd

ErrorsMode = Literal["raise", "coerce"]

_DATE_FORMATS: tuple[str, ...] = (
    "%Y/%m/%d",
    "%Y-%m-%d",
    "%Y%m%d",
)

_TIME_FORMATS: tuple[str, ...] = (
    "%H:%M:%S",
    "%H:%M",
    "%H%M%S",
)

_DATETIME_FORMATS: tuple[str, ...] = (
    # 含秒：空白或 ISO「T」分隔
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    # 僅到分：空白或 ISO「T」分隔
    "%Y/%m/%d %H:%M",
    "%Y-%m-%d %H:%M",
    "%Y/%m/%dT%H:%M",
    "%Y-%m-%dT%H:%M",
    # 緊湊 14 碼
    "%Y%m%d%H%M%S",
    # 含微秒
    "%Y/%m/%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y/%m/%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S.%f",
)

T = TypeVar("T")


def _is_missing(value: object) -> bool:
    """判斷是否為空值（``None``／``NaN``／``NaT``／空字串等）。"""
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    if isinstance(value, pd.Timestamp) and pd.isna(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, str) and value.strip().lower() in {"nan", "nat", "none"}:
        return True
    return False


def _as_text(value: object) -> str:
    """將值轉成待解析字串；數字尾端 ``.0``（Excel 常見）會先去掉。"""
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text


def _strptime_first(text: str, formats: tuple[str, ...]) -> datetime | None:
    """依序嘗試格式，成功則回傳 ``datetime``，否則 ``None``。"""
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _parse_date_value(value: object, *, errors: ErrorsMode) -> date | None:
    """將單一值解析為 ``datetime.date``。"""
    if _is_missing(value):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, time):
        if errors == "raise":
            raise ValueError(f"無法自純時間解析日期: {value!r}")
        return None

    text = _as_text(value)
    parsed = _strptime_first(text, _DATE_FORMATS)
    if parsed is not None:
        return parsed.date()

    # 若是完整日期時間字串，取日期部分
    parsed_dt = _strptime_first(text, _DATETIME_FORMATS)
    if parsed_dt is not None:
        return parsed_dt.date()

    fallback = pd.to_datetime(text, errors="coerce")
    if pd.isna(fallback):
        if errors == "raise":
            raise ValueError(f"無法解析為日期: {value!r}")
        return None
    return pd.Timestamp(fallback).date()


def _parse_time_value(value: object, *, errors: ErrorsMode) -> time | None:
    """將單一值解析為 ``datetime.time``。"""
    if _is_missing(value):
        return None
    if isinstance(value, time) and not isinstance(value, datetime):
        return value
    if isinstance(value, pd.Timestamp):
        return value.time()
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, date) and not isinstance(value, datetime):
        if errors == "raise":
            raise ValueError(f"無法自純日期解析時間: {value!r}")
        return None

    text = _as_text(value)
    parsed = _strptime_first(text, _TIME_FORMATS)
    if parsed is not None:
        return parsed.time()

    # 若是完整日期時間字串，取時間部分
    parsed_dt = _strptime_first(text, _DATETIME_FORMATS)
    if parsed_dt is not None:
        return parsed_dt.time()

    fallback = pd.to_datetime(text, errors="coerce")
    if pd.isna(fallback):
        if errors == "raise":
            raise ValueError(f"無法解析為時間: {value!r}")
        return None
    return pd.Timestamp(fallback).time()


def _parse_datetime_value(value: object, *, errors: ErrorsMode) -> pd.Timestamp:
    """將單一值解析為 ``pd.Timestamp``。"""
    if _is_missing(value):
        return pd.NaT
    if isinstance(value, pd.Timestamp):
        return value
    if isinstance(value, datetime):
        return pd.Timestamp(value)
    if isinstance(value, date) and not isinstance(value, datetime):
        return pd.Timestamp(value)
    if isinstance(value, time):
        if errors == "raise":
            raise ValueError(f"無法自純時間解析日期時間: {value!r}")
        return pd.NaT

    text = _as_text(value)
    parsed = _strptime_first(text, _DATETIME_FORMATS)
    if parsed is not None:
        return pd.Timestamp(parsed)

    # 僅有日期時，時間補 00:00:00
    parsed_date = _strptime_first(text, _DATE_FORMATS)
    if parsed_date is not None:
        return pd.Timestamp(parsed_date)

    fallback = pd.to_datetime(text, errors="coerce")
    if pd.isna(fallback):
        if errors == "raise":
            raise ValueError(f"無法解析為日期時間: {value!r}")
        return pd.NaT
    return pd.Timestamp(fallback)


def _transform_column(
    df: pd.DataFrame,
    column: str,
    *,
    result_col: str | None,
    errors: ErrorsMode,
    parser: Callable[[object], T],
) -> pd.DataFrame:
    """共用：驗證參數、複製 DataFrame、套用單一值 parser。"""
    if errors not in ("raise", "coerce"):
        raise ValueError(f"errors 須為 'raise' 或 'coerce'，收到 {errors!r}")
    if column not in df.columns:
        raise KeyError(f"欄位不存在: {column!r}")

    out = df.copy()
    target = column if result_col is None else result_col
    out[target] = [parser(v) for v in out[column]]
    return out


def to_date_column(
    df: pd.DataFrame,
    column: str,
    *,
    result_col: str | None = None,
    errors: ErrorsMode = "raise",
) -> pd.DataFrame:
    """將 DataFrame 指定欄位轉換為純日期（``datetime.date``）。

    支援常見字串格式，例如：

    - ``"2025/08/15"``、``"2025/8/15"``
    - ``"2025-08-15"``、``"2025-8-15"``
    - ``"20250815"``

    若值為完整日期時間字串，則只取日期部分。

    Parameters
    ----------
    df :
        輸入資料表。
    column :
        要轉換的欄位名稱（單位：不適用）。
    result_col :
        寫入結果的欄位名；預設 ``None`` 表示覆寫 ``column``（單位：不適用）。
    errors :
        解析失敗時的行為：``"raise"`` 拋出例外，``"coerce"`` 寫入 ``None``
        （單位：不適用）。

    Returns
    -------
    pd.DataFrame
        含純日期欄位的新 DataFrame（不修改原表）。欄位元素為 ``datetime.date``
        或空值 ``None``（單位：不適用）。

    Raises
    ------
    KeyError
        ``column`` 不存在於 ``df``。
    ValueError
        ``errors="raise"`` 且欄位中有無法解析的值；或 ``errors`` 非允許值。
    """
    return _transform_column(
        df,
        column,
        result_col=result_col,
        errors=errors,
        parser=lambda v: _parse_date_value(v, errors=errors),
    )


def to_time_column(
    df: pd.DataFrame,
    column: str,
    *,
    result_col: str | None = None,
    errors: ErrorsMode = "raise",
) -> pd.DataFrame:
    """將 DataFrame 指定欄位轉換為純時間（``datetime.time``）。

    支援常見字串格式，例如：

    - ``"14:00:15"``、``"14:00"``
    - ``"140015"``

    若值為完整日期時間字串，則只取時間部分。

    Parameters
    ----------
    df :
        輸入資料表。
    column :
        要轉換的欄位名稱（單位：不適用）。
    result_col :
        寫入結果的欄位名；預設 ``None`` 表示覆寫 ``column``（單位：不適用）。
    errors :
        解析失敗時的行為：``"raise"`` 拋出例外，``"coerce"`` 寫入 ``None``
        （單位：不適用）。

    Returns
    -------
    pd.DataFrame
        含純時間欄位的新 DataFrame（不修改原表）。欄位元素為 ``datetime.time``
        或空值 ``None``（單位：不適用）。

    Raises
    ------
    KeyError
        ``column`` 不存在於 ``df``。
    ValueError
        ``errors="raise"`` 且欄位中有無法解析的值；或 ``errors`` 非允許值。
    """
    return _transform_column(
        df,
        column,
        result_col=result_col,
        errors=errors,
        parser=lambda v: _parse_time_value(v, errors=errors),
    )


def to_datetime_column(
    df: pd.DataFrame,
    column: str,
    *,
    result_col: str | None = None,
    errors: ErrorsMode = "raise",
) -> pd.DataFrame:
    """將 DataFrame 指定欄位轉換為日期時間（``datetime64``）。

    支援常見字串格式，例如：

    - ``"2025/08/15 14:00:15"``、``"2025/8/15 14:00:15"``
    - ``"2025-08-15 14:00:15"``、``"2025-8-15 14:00:15"``
    - ``"2025/08/15T14:00:15"``、``"2025-08-15T14:00:15"``（ISO「T」分隔）
    - ``"2025-08-15T14:00"``、``"2025/08/15 14:00"``（僅到分）
    - ``"20250815140015"``

    若值僅有日期（無時間），時間會補為 ``00:00:00``。

    Parameters
    ----------
    df :
        輸入資料表。
    column :
        要轉換的欄位名稱（單位：不適用）。
    result_col :
        寫入結果的欄位名；預設 ``None`` 表示覆寫 ``column``（單位：不適用）。
    errors :
        解析失敗時的行為：``"raise"`` 拋出例外，``"coerce"`` 寫入 ``NaT``
        （單位：不適用）。

    Returns
    -------
    pd.DataFrame
        含日期時間欄位的新 DataFrame（不修改原表）。時間單位為納秒解析度的
        pandas Timestamp（顯示為年月日與時分秒）。

    Raises
    ------
    KeyError
        ``column`` 不存在於 ``df``。
    ValueError
        ``errors="raise"`` 且欄位中有無法解析的值；或 ``errors`` 非允許值。
    """
    return _transform_column(
        df,
        column,
        result_col=result_col,
        errors=errors,
        parser=lambda v: _parse_datetime_value(v, errors=errors),
    )
