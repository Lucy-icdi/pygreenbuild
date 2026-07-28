"""ChillerKPI／ChillerPerformance 單元測試。"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from pygreenbuild import ChillerKPI
from pygreenbuild.metrics.chiller_performance import ChillerPerformance


class TestTopLevelExport:
    def test_from_pygreenbuild_import(self) -> None:
        assert ChillerKPI is ChillerPerformance


class TestCalculateCop:
    def test_reference_example(self) -> None:
        # 2023/9/20 10:00：USRT=1149 → cooling_kw=1149/0.284，功率=643.95
        # COP ≈ 6.28
        cooling_kw = 1149.0 / ChillerKPI.KW_TO_USRT_FACTOR
        cop = ChillerKPI.calculate_cop(cooling_kw, 410.6 + 233.35)
        assert cop == pytest.approx(6.28, abs=0.01)

    def test_zero_returns_nan(self) -> None:
        assert math.isnan(ChillerKPI.calculate_cop(0, 100))
        assert math.isnan(ChillerKPI.calculate_cop(100, 0))


class TestCalculateEer:
    def test_reference_example(self) -> None:
        cooling_kw = 1149.0 / ChillerKPI.KW_TO_USRT_FACTOR
        eer = ChillerKPI.calculate_eer(cooling_kw, 643.95)
        # EER = cooling_kw × 0.86 / power ≈ 5.40
        assert eer == pytest.approx(cooling_kw * 0.86 / 643.95, abs=0.01)

    def test_zero_returns_nan(self) -> None:
        assert math.isnan(ChillerKPI.calculate_eer(0, 100))
        assert math.isnan(ChillerKPI.calculate_eer(100, 0))


class TestCalculatePowerRate:
    def test_from_usrt(self) -> None:
        # 耗電率 = 643.95 / 1149 ≈ 0.56
        rate = ChillerKPI.calculate_power_rate(643.95, usrt=1149.0)
        assert rate == pytest.approx(0.56, abs=0.01)

    def test_from_cooling_kw(self) -> None:
        cooling_kw = 1149.0 / ChillerKPI.KW_TO_USRT_FACTOR
        rate = ChillerKPI.calculate_power_rate(643.95, cooling_kw=cooling_kw)
        assert rate == pytest.approx(0.56, abs=0.01)

    def test_zero_usrt_returns_nan(self) -> None:
        assert math.isnan(ChillerKPI.calculate_power_rate(100, usrt=0))

    def test_requires_exactly_one_capacity(self) -> None:
        with pytest.raises(ValueError, match="cooling_kw 或 usrt"):
            ChillerKPI.calculate_power_rate(100)
        with pytest.raises(ValueError, match="cooling_kw 或 usrt"):
            ChillerKPI.calculate_power_rate(100, cooling_kw=10, usrt=10)


class TestCalculatePerformance:
    def test_dataframe_from_cooling_kw(self) -> None:
        cooling_kw = 1149.0 / ChillerKPI.KW_TO_USRT_FACTOR
        df = pd.DataFrame(
            {
                "冷房熱量_kW": [cooling_kw, 500.0],
                "CH_02": [410.6, 0.0],
                "CH_04": [233.35, 200.0],
                "CH_B01": [0.0, 0.0],
            }
        )
        out = ChillerKPI.calculate_performance(
            df,
            cooling_kw_col="冷房熱量_kW",
            power_cols=["CH_02", "CH_04", "CH_B01"],
            power_rate_from="cooling_kw",
        )
        assert "COP" in out.columns
        assert "EER" in out.columns
        assert "耗電率" in out.columns
        assert "輸入功率_kW" in out.columns
        assert "USRT" in out.columns
        assert out.loc[0, "輸入功率_kW"] == pytest.approx(643.95)
        assert out.loc[0, "COP"] == pytest.approx(6.28, abs=0.01)
        assert out.loc[0, "耗電率"] == pytest.approx(0.56, abs=0.01)
