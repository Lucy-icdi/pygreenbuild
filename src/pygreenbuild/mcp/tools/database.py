"""資料庫唯讀 MCP tools。"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from pygreenbuild.api.services.database import fill_sql_table_na_service


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
        return fill_sql_table_na_service(
            table_name,
            range_col=range_col,
            range_start=range_start,
            range_end=range_end,
            exclude_cols=exclude_cols,
            key_cols=key_cols,
            fill_method=fill_method,
            fill_value=fill_value,
            columns=columns,
        )
