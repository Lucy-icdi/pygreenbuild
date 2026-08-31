"""資料庫唯讀服務層。"""

from __future__ import annotations

import os
from typing import Any

from pygreenbuild.api.serialization import wrap_failure, wrap_success
from pygreenbuild.ingestion.ems_db.factory_db import fill_sql_table_na


def _resolve_db_url(connection_str: str | None) -> str | None:
    """從參數或環境變數取得資料庫連線字串。"""
    if connection_str:
        return connection_str
    return os.environ.get("PYGREENBUILD_DB_URL")


def fill_sql_table_na_service(
    table_name: str,
    *,
    range_col: str | None = None,
    range_start: Any = None,
    range_end: Any = None,
    exclude_cols: list[str] | None = None,
    key_cols: list[str] | None = None,
    fill_method: str = "neighbor_mean",
    fill_value: object | None = None,
    columns: list[str] | None = None,
) -> dict[str, Any]:
    """從資料庫讀表、填補孤立 NA 並回傳預覽（不回寫 DB）。

    連線字串從 ``PYGREENBUILD_DB_URL`` 環境變數讀取，不允許 tool 參數直接傳入。

    Parameters
    ----------
    table_name :
        資料表名稱（單位：不適用）。
    range_col, range_start, range_end :
        可選範圍篩選（單位：依欄位而定）。
    exclude_cols :
        不參與填補的欄位（單位：不適用）。
    key_cols :
        回傳定位欄（單位：不適用）。
    fill_method :
        填值策略（單位：不適用）。
    fill_value :
        ``fill_method="constant"`` 時使用（單位：依欄位而定）。
    columns :
        只填這些欄（單位：不適用）。

    Returns
    -------
    dict[str, Any]
        含 ``success``、``message``、``result``（fill_sql_table_na 回傳 dict）
        （單位：不適用）。
    """
    connection_str = _resolve_db_url(None)
    if not connection_str:
        return wrap_failure("請設定 PYGREENBUILD_DB_URL 環境變數")

    try:
        result = fill_sql_table_na(
            connection_str,
            table_name,
            range_col,
            range_start,
            range_end,
            exclude_cols=exclude_cols,
            key_cols=key_cols,
            fill_method=fill_method,  # type: ignore[arg-type]
            fill_value=fill_value,
            columns=columns,
        )
    except Exception as exc:
        return wrap_failure(str(exc))

    return wrap_success(result)
