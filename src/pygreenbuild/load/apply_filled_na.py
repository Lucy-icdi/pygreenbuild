"""將 ``fill_sql_table_na`` 的填補結果寫回資料庫，或匯出 UPDATE SQL 檔。"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from pygreenbuild.ingestion.ems_db.factory_db import _validate_identifier


def _sql_literal(value: Any) -> str:
    """將 Python 值轉成 SQL 字面常數（供 SQL 檔使用）。"""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(int(value))
    if isinstance(value, float):
        # 避免 float 雜訊；沿用 str → Decimal 的可見位數
        return format(Decimal(str(value)), "f")
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace("'", "''")
        return f"'{escaped}'"
    # datetime / date 等
    text_val = str(value)
    escaped = text_val.replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def _split_record(
    record: dict[str, Any], key_cols: list[str]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """拆成 WHERE 鍵值與 SET 欄位值。"""
    missing_keys = [k for k in key_cols if k not in record]
    if missing_keys:
        raise KeyError(f"records 缺少 key_cols: {missing_keys}")
    where_vals = {k: record[k] for k in key_cols}
    set_vals = {k: v for k, v in record.items() if k not in key_cols}
    if not set_vals:
        raise ValueError(
            f"record 在 key_cols 之外沒有可更新欄位: {record!r}"
        )
    for col in set_vals:
        _validate_identifier(col, kind="更新欄位")
    return where_vals, set_vals


def _build_update_sql(
    table: str,
    where_vals: dict[str, Any],
    set_vals: dict[str, Any],
    *,
    quote,
) -> tuple[str, dict[str, Any]]:
    """組出參數化 UPDATE 與綁定參數。"""
    q_table = quote(table)
    set_parts: list[str] = []
    where_parts: list[str] = []
    params: dict[str, Any] = {}

    for i, (col, val) in enumerate(set_vals.items()):
        pname = f"set_{i}"
        set_parts.append(f"{quote(col)} = :{pname}")
        params[pname] = val

    for i, (col, val) in enumerate(where_vals.items()):
        pname = f"where_{i}"
        where_parts.append(f"{quote(col)} = :{pname}")
        params[pname] = val

    sql = (
        f"UPDATE {q_table} SET {', '.join(set_parts)} "
        f"WHERE {' AND '.join(where_parts)}"
    )
    return sql, params


def _build_update_sql_literal(
    table: str,
    where_vals: dict[str, Any],
    set_vals: dict[str, Any],
    *,
    quote,
) -> str:
    """組出含字面常數的 UPDATE（寫入 SQL 檔）。"""
    q_table = quote(table)
    set_clause = ", ".join(
        f"{quote(col)} = {_sql_literal(val)}" for col, val in set_vals.items()
    )
    where_clause = " AND ".join(
        f"{quote(col)} = {_sql_literal(val)}" for col, val in where_vals.items()
    )
    return f"UPDATE {q_table} SET {set_clause} WHERE {where_clause};"


def _validate_result(result: dict[str, Any]) -> tuple[str, list[str], list[dict]]:
    """檢查 ``fill_sql_table_na`` 回傳結構並取出必要欄位。"""
    if not isinstance(result, dict):
        raise TypeError(f"result 須為 dict，收到 {type(result)!r}")
    if "table_name" not in result or "records" not in result:
        raise KeyError("result 須含 table_name 與 records（fill_sql_table_na 輸出）")
    key_cols = result.get("key_cols")
    if not key_cols:
        raise ValueError(
            "result['key_cols'] 不可為空；寫回資料庫需要定位欄 "
            "（請在 fill_sql_table_na 指定 key_cols）"
        )
    table = _validate_identifier(result["table_name"], kind="table_name")
    keys = [_validate_identifier(c, kind="key_cols 項目") for c in key_cols]
    records = result["records"]
    if not isinstance(records, list):
        raise TypeError(f"result['records'] 須為 list，收到 {type(records)!r}")
    return table, keys, records


def _preview_statements(statements: list[str], *, limit: int = 5) -> None:
    """將前 ``limit`` 筆 UPDATE 印到標準輸出。"""
    total = len(statements)
    show = statements[:limit]
    print(f"[apply_filled_na] 共 {total} 筆 UPDATE，預覽前 {len(show)} 筆：")
    for i, stmt in enumerate(show, start=1):
        print(f"  {i}. {stmt}")
    if total > limit:
        print(f"  ... 其餘 {total - limit} 筆已寫入 SQL 檔")


def apply_filled_na(
    result: dict[str, Any],
    connection_str: str | None = None,
    *,
    sql_only: bool = False,
    sql_path: str | Path | None = None,
    engine: Engine | None = None,
) -> dict[str, Any]:
    """將 ``fill_sql_table_na`` 結果依 ``key_cols`` 寫回資料庫或匯出 SQL。

    對 ``result["records"]`` 每一列產生 ``UPDATE``：``SET`` 填補欄、
    ``WHERE`` 對應 ``key_cols``。

    Parameters
    ----------
    result :
        ``fill_sql_table_na`` 的回傳 dict，須含 ``table_name``、``key_cols``、
        ``records``（單位：不適用）。
    connection_str :
        SQLAlchemy 連線字串；``sql_only=False`` 且未傳 ``engine`` 時必填
        （單位：不適用）。
    sql_only :
        ``True``：只寫出 SQL 指令檔、不連線執行，並在標準輸出預覽前 5 筆
        UPDATE；``False``：直接對資料庫執行 UPDATE（單位：不適用）。
        預設 ``False``。
    sql_path :
        SQL 檔路徑；``sql_only=True`` 時可省略，預設
        ``{table_name}_filled_na.sql``（單位：不適用）。
        ``sql_only=False`` 時若有給定，仍會順便寫出同一份 SQL 供留存。
    engine :
        可選既有 ``Engine``；若提供則不依 ``connection_str`` 新建
        （單位：不適用）。

    Returns
    -------
    dict[str, Any]
        - ``table_name`` (``str``)
        - ``sql_only`` (``bool``)
        - ``sql_path`` (``str | None``)：有寫檔時為路徑字串
        - ``n_statements`` (``int``)：UPDATE 筆數
        - ``n_rowcount`` (``int | None``)：執行時受影響列數合計；僅匯出時為 ``None``
        - ``statements`` (``list[str]``)：產生的 UPDATE 語句（含分號）

    Raises
    ------
    TypeError
        ``result``／``records`` 型別錯誤。
    KeyError
        缺少必要鍵，或 record 缺少 ``key_cols``。
    ValueError
        未指定 ``key_cols``、record 無可更新欄、``sql_only=False`` 卻無連線、
        或識別字非法。
    sqlalchemy.exc.SQLAlchemyError
        執行 UPDATE 失敗時由 SQLAlchemy 拋出。
    """
    table, key_cols, records = _validate_result(result)

    if not records:
        out_path: str | None = None
        if sql_only:
            path = Path(sql_path) if sql_path else Path(f"{table}_filled_na.sql")
            path.write_text(
                f"-- fill_sql_table_na apply: {table} (no records)\n",
                encoding="utf-8",
            )
            out_path = str(path)
        return {
            "table_name": table,
            "sql_only": sql_only,
            "sql_path": out_path,
            "n_statements": 0,
            "n_rowcount": 0 if not sql_only else None,
            "statements": [],
        }

    # 組字面 SQL（檔案與回傳）；quoting 採 MySQL 風格 backtick，
    # 執行時另用實際 dialect 的 preparer。
    def _mysql_quote(name: str) -> str:
        return f"`{name.replace('`', '``')}`"

    literal_statements: list[str] = []
    parsed: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for rec in records:
        if not isinstance(rec, dict):
            raise TypeError(f"records 項目須為 dict，收到 {type(rec)!r}")
        where_vals, set_vals = _split_record(rec, key_cols)
        parsed.append((where_vals, set_vals))
        literal_statements.append(
            _build_update_sql_literal(
                table, where_vals, set_vals, quote=_mysql_quote
            )
        )

    out_path = None
    if sql_only or sql_path is not None:
        path = Path(sql_path) if sql_path else Path(f"{table}_filled_na.sql")
        header = (
            f"-- Generated by apply_filled_na for table `{table}`\n"
            f"-- statements: {len(literal_statements)}\n"
        )
        path.write_text(
            header + "\n".join(literal_statements) + "\n",
            encoding="utf-8",
        )
        out_path = str(path)

    if sql_only:
        _preview_statements(literal_statements, limit=5)
        return {
            "table_name": table,
            "sql_only": True,
            "sql_path": out_path,
            "n_statements": len(literal_statements),
            "n_rowcount": None,
            "statements": literal_statements,
        }

    if engine is None and not connection_str:
        raise ValueError(
            "sql_only=False 時必須提供 connection_str 或 engine"
        )

    own_engine = engine is None
    eng = engine if engine is not None else create_engine(connection_str)
    quote = eng.dialect.identifier_preparer.quote
    total_rowcount = 0

    try:
        with eng.begin() as conn:
            for where_vals, set_vals in parsed:
                sql, params = _build_update_sql(
                    table, where_vals, set_vals, quote=quote
                )
                result_proxy = conn.execute(text(sql), params)
                # rowcount 在部分 driver 可能為 -1
                rc = result_proxy.rowcount
                if rc is not None and rc >= 0:
                    total_rowcount += int(rc)
    finally:
        if own_engine:
            eng.dispose()

    return {
        "table_name": table,
        "sql_only": False,
        "sql_path": out_path,
        "n_statements": len(literal_statements),
        "n_rowcount": total_rowcount,
        "statements": literal_statements,
    }
