"""MCP Server 單元測試。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from pygreenbuild.mcp.serialization import (
    dataframe_to_records,
    records_to_dataframe,
    wrap_failure,
    wrap_success,
)
from pygreenbuild.mcp.server import mcp


def _tool_fn(name: str) -> Callable[..., Any]:
    """從已註冊的 FastMCP tools 取出可呼叫函式。"""
    for tool in mcp._tool_manager.list_tools():  # noqa: SLF001
        if tool.name == name:
            return tool.fn
    raise KeyError(name)


class TestSerialization:
    def test_dataframe_roundtrip(self) -> None:
        import pandas as pd

        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        records = dataframe_to_records(df)
        assert records["format"] == "records"
        assert records["row_count"] == 2
        assert records["columns"] == ["a", "b"]

        restored = records_to_dataframe(records["data"])
        pd.testing.assert_frame_equal(restored, df)

    def test_records_to_dataframe_rejects_empty(self) -> None:
        with pytest.raises(ValueError, match="不可為空"):
            records_to_dataframe([])

    def test_wrap_helpers(self) -> None:
        ok = wrap_success({"x": 1}, message="done")
        assert ok["success"] is True
        assert ok["result"] == {"x": 1}

        fail = wrap_failure("error")
        assert fail["success"] is False
        assert fail["result"] is None


class TestTransformTools:
    def test_json_to_dataframe(self) -> None:
        data = [
            {
                "DataTime": "2024-01-01T00:00:00",
                "WeatherElement": {
                    "AirTemperature": {"Meaning": "25.0"},
                },
            }
        ]
        result = _tool_fn("json_to_dataframe")(data)
        assert result["success"] is True
        assert result["result"]["row_count"] == 1
        assert "觀測時間" in result["result"]["columns"]

    def test_fill_dataframe_na(self) -> None:
        data = [
            {"DateTime": 1, "temp": 20.0, "hum": 50.0},
            {"DateTime": 2, "temp": None, "hum": 55.0},
            {"DateTime": 3, "temp": 24.0, "hum": None},
            {"DateTime": 4, "temp": 25.0, "hum": 65.0},
        ]
        result = _tool_fn("fill_dataframe_na")(data, exclude_cols=["DateTime"])
        assert result["success"] is True
        assert result["result"]["data"][1]["temp"] == 22.0
        assert result["result"]["data"][2]["hum"] == 60.0

    def test_pmv_iso(self) -> None:
        result = _tool_fn("pmv_iso")(
            tdb=25.0,
            tr=25.0,
            vr=0.1,
            rh=50.0,
            met=1.2,
            clo=0.5,
        )
        assert result["success"] is True
        assert "pmv" in result["result"]
        assert "ppd" in result["result"]


class TestMetricsTools:
    def test_chiller_usrt_single(self) -> None:
        result = _tool_fn("chiller_usrt_single")(
            flow_rate=17.49,
            flow_unit="CMH",
            return_temp=13.28,
            return_temp_unit="C",
            supply_temp=8.86,
            supply_temp_unit="C",
            kw_to_usrt=False,
        )
        assert result["success"] is True
        assert result["result"] > 0

    def test_chiller_cop(self) -> None:
        result = _tool_fn("chiller_cop")(cooling_kw=1000.0, power_kw=200.0)
        assert result["success"] is True
        assert result["result"] == 5.0


class TestDatabaseTool:
    def test_fill_sql_table_na_requires_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PYGREENBUILD_DB_URL", raising=False)
        result = _tool_fn("fill_sql_table_na")("some_table")
        assert result["success"] is False
        assert "PYGREENBUILD_DB_URL" in result["message"]


class TestWeatherTool:
    def test_cwa_forecast_requires_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CWA_API_KEY", raising=False)
        result = _tool_fn("cwa_township_forecast_3day")()
        assert result["success"] is False
        assert "CWA_API_KEY" in result["message"]


class TestMcpServer:
    def test_server_has_tools_registered(self) -> None:
        tool_names = {t.name for t in mcp._tool_manager.list_tools()}  # noqa: SLF001
        expected = {
            "codis_daily",
            "codis_monthly",
            "codis_yearly",
            "codis_single_hourly_monthly",
            "codis_single_daily_yearly",
            "codis_single_monthly_yearly",
            "cwa_township_forecast_3day",
            "cwa_township_forecast_week",
            "json_to_dataframe",
            "fill_time_gaps",
            "fill_dataframe_na",
            "pmv_iso",
            "pmv_ashrae",
            "chiller_cop",
            "chiller_usrt_single",
            "fill_sql_table_na",
        }
        assert expected.issubset(tool_names)

    def test_server_name(self) -> None:
        assert mcp.name == "pygreenbuild"
