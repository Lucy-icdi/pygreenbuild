"""從 EMS／廠區資料庫讀取表單並填補孤立 NA，回傳可供寫回的 dict。"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from pygreenbuild.transform.fill_na_result import build_filled_na_result
from pygreenbuild.transform.fill_surrounded_na import FillSurroundedMethod

_UNSAFE_IDENT_RE = re.compile('[`"\';\x00-\x1f\x7f]')


def _validate_identifier(name: str, *, kind: str) -> str:
    """驗證資料表／欄位名稱為可安全 quoting 的識別字（僅用於組 SQL）。"""
    if not isinstance(name, str) or not name or name != name.strip():
        raise ValueError(f"{kind} 須為非空且無頭尾空白的識別字，收到 {name!r}")
    if _UNSAFE_IDENT_RE.search(name):
        raise ValueError(
            f"{kind} 含非法字元（引號、分號或控制字元），收到 {name!r}"
        )
    return name


def fill_sql_table_na(
    connection_str: str,
    table_name: str,
    range_col: str | None = None,
    range_start: Any = None,
    range_end: Any = None,
    *,
    exclude_cols: list[str] | None = None,
    key_cols: list[str] | None = None,
    fill_method: FillSurroundedMethod = "neighbor_mean",
    fill_value: object | None = None,
    columns: list[str] | None = None,
    engine: Engine | None = None,
) -> dict[str, Any]:
    """連線資料庫、查詢表單，填補孤立 NA 後回傳 dict。

    僅從資料庫讀取。若資料已在記憶體，請改用 ``fill_dataframe_na``。

    若 ``range_col``／``range_start``／``range_end`` 皆省略，讀取整張表；
    若要篩選範圍，三者須同時指定。有指定範圍時，結果依該欄升冪排序。

    Parameters
    ----------
    connection_str :
        SQLAlchemy 連線字串（單位：不適用）。已傳 ``engine`` 時可忽略實際連線。
    table_name :
        資料表名稱（單位：不適用）。
    range_col / range_start / range_end :
        可選範圍篩選（單位：依欄位而定）。
    exclude_cols :
        不參與填補的欄位（單位：不適用）。
    key_cols :
        回傳定位欄；有給則精簡 ``records``（單位：不適用）。
    fill_method :
        填值策略（單位：不適用）。
    fill_value :
        ``fill_method="constant"`` 時使用（單位：依欄位而定）。
    columns :
        只填這些欄；``None`` 表示除排除欄外全部欄位（單位：不適用）。
    engine :
        可選既有 ``Engine``（單位：不適用）。

    Returns
    -------
    dict[str, Any]
        含 ``table_name``、``records``、``n_filled_cells`` 等（單位：不適用）。

    Raises
    ------
    ValueError
        表名／範圍欄含非法識別字，或範圍三參數不完整。
    """
    table = _validate_identifier(table_name, kind="table_name")
    provided = [
        range_col is not None,
        range_start is not None,
        range_end is not None,
    ]
    if any(provided) and not all(provided):
        raise ValueError(
            "range_col、range_start、range_end 須同時指定，"
            "或全部省略以讀取整張表"
        )
    rcol = (
        _validate_identifier(range_col, kind="range_col")
        if range_col is not None
        else None
    )

    own_engine = engine is None
    eng = engine if engine is not None else create_engine(connection_str)

    preparer = eng.dialect.identifier_preparer
    q_table = preparer.quote(table)
    if rcol is None:
        sql = text(f"SELECT * FROM {q_table}")
        params: dict[str, Any] | None = None
    else:
        q_col = preparer.quote(rcol)
        sql = text(
            f"SELECT * FROM {q_table} "
            f"WHERE {q_col} BETWEEN :range_start AND :range_end "
            f"ORDER BY {q_col} ASC"
        )
        params = {"range_start": range_start, "range_end": range_end}

    try:
        with eng.connect() as conn:
            df = pd.read_sql(sql, conn, params=params)
    finally:
        if own_engine:
            eng.dispose()

    return build_filled_na_result(
        df,
        table_name=table,
        range_col=rcol,
        range_start=range_start,
        range_end=range_end,
        exclude_cols=exclude_cols,
        key_cols=key_cols,
        fill_method=fill_method,
        fill_value=fill_value,
        columns=columns,
    )
