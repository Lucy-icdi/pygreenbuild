"""資料庫唯讀 MCP tools。"""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from pygreenbuild.ingestion.ems_db.factory_db import (
    fill_sql_table_na as _fill_sql_table_na,
)
from pygreenbuild.mcp.serialization import wrap_failure, wrap_success


def register_database_tools(mcp: FastMCP) -> None:
    """註冊資料庫唯讀 tools。"""

    @mcp.tool()
    def fill_sql_table_na(
        table_name: str,
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

        連線字串從 PYGREENBUILD_DB_URL 環境變數讀取。
        """
        connection_str = os.environ.get("PYGREENBUILD_DB_URL")
        if not connection_str:
            return wrap_failure("請設定 PYGREENBUILD_DB_URL 環境變數")

        try:
            result = _fill_sql_table_na(
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
