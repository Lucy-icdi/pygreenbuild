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

_DATE_OUT_FMT = "%Y-%m-%d"
_TIME_OUT_FMT = "%H:%M:%S"
_DATETIME_OUT_FMT = "%Y-%m-%d %H:%M:%S"

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


def _is_2359(hour: int, minute: int) -> bool:
    """判斷是否為 ``23:59`` 這一分鐘（秒／微秒不論）。"""
    return hour == 23 and minute == 59


def _roll_past_2359_timestamp(ts: pd.Timestamp) -> pd.Timestamp:
    """``23:59:00``–``23:59:59`` 視為隔天 ``00:00:00``。"""
    if pd.isna(ts):
        return ts
    if _is_2359(ts.hour, ts.minute):
        return ts.normalize() + pd.Timedelta(days=1)
    return ts


def _roll_past_2359_time(t: time) -> time:
    """``23:59:00``–``23:59:59`` 視為 ``00:00:00``。"""
    if _is_2359(t.hour, t.minute):
        return time(0, 0, 0)
    return t


def _roll_past_2359_series(series: pd.Series) -> pd.Series:
    """對 datetime 序列套用與 ``_roll_past_2359_timestamp`` 相同的規則。"""
    ts = pd.to_datetime(series)
    mask = (ts.dt.hour == 23) & (ts.dt.minute == 59)
    out = ts.copy()
    out.loc[mask] = ts.loc[mask].dt.normalize() + pd.Timedelta(days=1)
    return out


def _format_date_value(value: date | None, *, as_string: bool) -> date | str | None:
    """依 ``as_string`` 決定回傳 ``date`` 或 ``YYYY-MM-DD`` 字串。"""
    if value is None:
        return None
    if as_string:
        return value.strftime(_DATE_OUT_FMT)
    return value


def _format_time_value(value: time | None, *, as_string: bool) -> time | str | None:
    """依 ``as_string`` 決定回傳 ``time`` 或 ``HH:MM:SS`` 字串。"""
    if value is None:
        return None
    if as_string:
        return value.strftime(_TIME_OUT_FMT)
    return value


def _format_datetime_value(
    value: pd.Timestamp, *, as_string: bool
) -> pd.Timestamp | str | None:
    """依 ``as_string`` 決定回傳 ``Timestamp`` 或 ``YYYY-MM-DD HH:MM:SS`` 字串。"""
    if pd.isna(value):
        return None if as_string else value
    if as_string:
        return pd.Timestamp(value).strftime(_DATETIME_OUT_FMT)
    return value


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
    """將單一值解析為 ``datetime.time``。

    ``23:59:00``–``23:59:59`` 視為 ``00:00:00``（代表隔天午夜）。
    """
    if _is_missing(value):
        return None
    if isinstance(value, time) and not isinstance(value, datetime):
        return _roll_past_2359_time(value)
    if isinstance(value, pd.Timestamp):
        return _roll_past_2359_time(value.time())
    if isinstance(value, datetime):
        return _roll_past_2359_time(value.time())
    if isinstance(value, date) and not isinstance(value, datetime):
        if errors == "raise":
            raise ValueError(f"無法自純日期解析時間: {value!r}")
        return None

    text = _as_text(value)
    parsed = _strptime_first(text, _TIME_FORMATS)
    if parsed is not None:
        return _roll_past_2359_time(parsed.time())

    # 若是完整日期時間字串，取時間部分
    parsed_dt = _strptime_first(text, _DATETIME_FORMATS)
    if parsed_dt is not None:
        return _roll_past_2359_time(parsed_dt.time())

    fallback = pd.to_datetime(text, errors="coerce")
    if pd.isna(fallback):
        if errors == "raise":
            raise ValueError(f"無法解析為時間: {value!r}")
        return None
    return _roll_past_2359_time(pd.Timestamp(fallback).time())


def _parse_datetime_value(value: object, *, errors: ErrorsMode) -> pd.Timestamp:
    """將單一值解析為 ``pd.Timestamp``。

    ``23:59:00``–``23:59:59`` 視為隔天 ``00:00:00``。
    """
    if _is_missing(value):
        return pd.NaT
    if isinstance(value, pd.Timestamp):
        return _roll_past_2359_timestamp(value)
    if isinstance(value, datetime):
        return _roll_past_2359_timestamp(pd.Timestamp(value))
    if isinstance(value, date) and not isinstance(value, datetime):
        return pd.Timestamp(value)
    if isinstance(value, time):
        if errors == "raise":
            raise ValueError(f"無法自純時間解析日期時間: {value!r}")
        return pd.NaT

    text = _as_text(value)
    parsed = _strptime_first(text, _DATETIME_FORMATS)
    if parsed is not None:
        return _roll_past_2359_timestamp(pd.Timestamp(parsed))

    # 僅有日期時，時間補 00:00:00
    parsed_date = _strptime_first(text, _DATE_FORMATS)
    if parsed_date is not None:
        return pd.Timestamp(parsed_date)

    fallback = pd.to_datetime(text, errors="coerce")
    if pd.isna(fallback):
        if errors == "raise":
            raise ValueError(f"無法解析為日期時間: {value!r}")
        return pd.NaT
    return _roll_past_2359_timestamp(pd.Timestamp(fallback))


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
    as_string: bool = False,
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
    as_string :
        ``True`` 時輸出 ``YYYY-MM-DD`` 字串；``False``（預設）維持 ``datetime.date``
        （單位：不適用）。

    Returns
    -------
    pd.DataFrame
        含純日期欄位的新 DataFrame（不修改原表）。欄位元素為 ``datetime.date``、
        字串（``as_string=True``）或空值 ``None``（單位：不適用）。

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
        parser=lambda v: _format_date_value(
            _parse_date_value(v, errors=errors), as_string=as_string
        ),
    )


def to_time_column(
    df: pd.DataFrame,
    column: str,
    *,
    result_col: str | None = None,
    errors: ErrorsMode = "raise",
    as_string: bool = False,
) -> pd.DataFrame:
    """將 DataFrame 指定欄位轉換為純時間（``datetime.time``）。

    支援常見字串格式，例如：

    - ``"14:00:15"``、``"14:00"``
    - ``"140015"``

    若值為完整日期時間字串，則只取時間部分。

    特殊規則：``23:59:00``–``23:59:59`` 視為 ``00:00:00``
    （該分鐘代表隔天午夜，例如 ``23:59:01`` → ``00:00:00``）。

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
    as_string :
        ``True`` 時輸出 ``HH:MM:SS`` 字串；``False``（預設）維持 ``datetime.time``
        （單位：不適用）。

    Returns
    -------
    pd.DataFrame
        含純時間欄位的新 DataFrame（不修改原表）。欄位元素為 ``datetime.time``、
        字串（``as_string=True``）或空值 ``None``（單位：不適用）。

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
        parser=lambda v: _format_time_value(
            _parse_time_value(v, errors=errors), as_string=as_string
        ),
    )


def to_datetime_column(
    df: pd.DataFrame,
    column: str,
    *,
    result_col: str | None = None,
    errors: ErrorsMode = "raise",
    as_string: bool = False,
) -> pd.DataFrame:
    """將 DataFrame 指定欄位轉換為日期時間（``datetime64``）。

    支援常見字串格式，例如：

    - ``"2025/08/15 14:00:15"``、``"2025/8/15 14:00:15"``
    - ``"2025-08-15 14:00:15"``、``"2025-8-15 14:00:15"``
    - ``"2025/08/15T14:00:15"``、``"2025-08-15T14:00:15"``（ISO「T」分隔）
    - ``"2025-08-15T14:00"``、``"2025/08/15 14:00"``（僅到分）
    - ``"20250815140015"``

    若值僅有日期（無時間），時間會補為 ``00:00:00``。

    特殊規則：``23:59:00``–``23:59:59`` 視為隔天 ``00:00:00``
    （例如 ``2025-08-15 23:59:01`` → ``2025-08-16 00:00:00``）。

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
    as_string :
        ``True`` 時輸出 ``YYYY-MM-DD HH:MM:SS`` 字串；``False``（預設）維持
        ``datetime64``／``Timestamp``（單位：不適用）。

    Returns
    -------
    pd.DataFrame
        含日期時間欄位的新 DataFrame（不修改原表）。``as_string=False`` 時為納秒
        解析度的 pandas Timestamp；``as_string=True`` 時為字串（空值為 ``None``）。

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
        parser=lambda v: _format_datetime_value(
            _parse_datetime_value(v, errors=errors), as_string=as_string
        ),
    )

