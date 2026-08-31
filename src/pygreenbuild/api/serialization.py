"""DataFrame 與 MCP 可序列化格式之間的轉換。"""

from __future__ import annotations

from typing import Any

import pandas as pd

LARGE_RESULT_ROW_THRESHOLD = 5000


def dataframe_to_records(df: pd.DataFrame) -> dict[str, Any]:
    """將 DataFrame 轉為 MCP 可回傳的 JSON records 格式。

    Parameters
    ----------
    df :
        輸入資料表（單位：不適用）。

    Returns
    -------
    dict[str, Any]
        含 ``format``、``columns``、``data``、``row_count``（單位：不適用）。
    """
    return {
        "format": "records",
        "columns": list(df.columns),
        "data": df.to_dict(orient="records"),
        "row_count": len(df),
    }


def records_to_dataframe(data: list[dict[str, Any]]) -> pd.DataFrame:
    """將 JSON records 轉為 DataFrame。

    Parameters
    ----------
    data :
        每列為一個 dict 的列表（單位：不適用）。

    Returns
    -------
    pd.DataFrame
        還原後的資料表（單位：不適用）。

    Raises
    ------
    TypeError
        ``data`` 不是 list。
    ValueError
        ``data`` 為空 list。
    """
    if not isinstance(data, list):
        raise TypeError("data 必須為 list[dict]")
    if not data:
        raise ValueError("data 不可為空 list")
    return pd.DataFrame(data)


def dataframes_dict_to_records(results: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """將 ``{station_id: DataFrame}`` 轉為 MCP 可回傳格式。

    Parameters
    ----------
    results :
        測站 ID 到 DataFrame 的對應（單位：不適用）。

    Returns
    -------
    dict[str, Any]
        含 ``format``、``stations``（各測站 records 摘要）（單位：不適用）。
    """
    stations: dict[str, Any] = {}
    for station_id, df in results.items():
        stations[station_id] = dataframe_to_records(df)
    return {
        "format": "stations",
        "station_count": len(stations),
        "stations": stations,
    }


def wrap_success(result: Any, *, message: str = "ok") -> dict[str, Any]:
    """包裝成功回傳值為統一 dict 格式。"""
    return {"success": True, "message": message, "result": result}


def wrap_failure(message: str) -> dict[str, Any]:
    """包裝失敗回傳為統一 dict 格式。"""
    return {"success": False, "message": message, "result": None}
