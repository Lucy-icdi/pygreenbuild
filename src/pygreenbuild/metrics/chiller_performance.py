"""冰水主機成效計算：COP、耗電率。

參考公式（IPMVP／廠區實務）::

    製冷能力 (kW) = USRT / 0.284
    COP           = 製冷能力 (kW) / 輸入功率 (kW)
    耗電率        = 輸入功率 (kW) / 製冷能力 (USRT)

USRT 由 ``chiller_usrt.ChillerUSRT`` 先行求出後傳入。
"""

from __future__ import annotations

import math

import pandas as pd

from .chiller_usrt import ChillerUSRT


class ChillerPerformance:
    """冰水主機 COP／耗電率計算器。"""

    # 與 ChillerUSRT 一致：1 kW ≈ 0.284 USRT → 製冷能力 kW = USRT / 0.284
    KW_TO_USRT_FACTOR = ChillerUSRT.KW_TO_USRT_FACTOR

    # ------------------------------------------------------------------
    # 1. COP
    # ------------------------------------------------------------------
    @classmethod
    def calculate_cop(cls, usrt: float, power_kw: float) -> float:
        """計算 COP（能效比）。

        COP = 製冷能力(kW) / 輸入功率(kW)
            = (USRT / 0.284) / power_kw

        Parameters
        ----------
        usrt :
            冷房需求（USRT），由 ``ChillerUSRT`` 計算得出。
        power_kw :
            冰機輸入功率合計（kW），例如 CH_02 + CH_04。
        """
        if usrt <= 0 or power_kw <= 0 or math.isnan(usrt) or math.isnan(power_kw):
            return float("nan")
        cooling_kw = usrt / cls.KW_TO_USRT_FACTOR
        return cooling_kw / power_kw

    # ------------------------------------------------------------------
    # 2. 耗電率（kW / USRT）
    # ------------------------------------------------------------------
    @classmethod
    def calculate_power_rate(cls, usrt: float, power_kw: float) -> float:
        """計算耗電率（kW/USRT）。

        耗電率 = 輸入功率(kW) / 製冷能力(USRT)

        Parameters
        ----------
        usrt :
            冷房需求（USRT）。
        power_kw :
            冰機輸入功率合計（kW）。
        """
        if usrt <= 0 or power_kw < 0 or math.isnan(usrt) or math.isnan(power_kw):
            return float("nan")
        return power_kw / usrt

    # ------------------------------------------------------------------
    # 3. DataFrame 批次計算 COP + 耗電率
    # ------------------------------------------------------------------
    @classmethod
    def calculate_performance(
        cls,
        df: pd.DataFrame,
        *,
        usrt_col: str = "USRT",
        power_cols: list[str] | str,
        cop_col: str = "COP",
        power_rate_col: str = "耗電率",
        total_power_col: str | None = "輸入功率_kW",
    ) -> pd.DataFrame:
        """對 DataFrame 逐列計算 COP、耗電率，結果併回原表。

        Parameters
        ----------
        df :
            需含 USRT 欄，以及一或多個功率欄（kW）。
        usrt_col :
            USRT 欄位名（可由 ``ChillerUSRT.calculate_usrts`` 產出）。
        power_cols :
            功率欄位名，可為單一欄位字串或多欄 list（會加總）。
            例：``["CH_02", "CH_04", "CH_B01"]``。
        cop_col :
            COP 結果欄位名。
        power_rate_col :
            耗電率結果欄位名。
        total_power_col :
            若給定，會寫入功率加總欄；設 ``None`` 則不輸出。
        """
        out = df.copy()

        if isinstance(power_cols, str):
            power_cols = [power_cols]

        total_power = out[power_cols].sum(axis=1)
        if total_power_col is not None:
            out[total_power_col] = total_power

        out[cop_col] = [
            cls.calculate_cop(float(u), float(p))
            for u, p in zip(out[usrt_col], total_power, strict=True)
        ]
        out[power_rate_col] = [
            cls.calculate_power_rate(float(u), float(p))
            for u, p in zip(out[usrt_col], total_power, strict=True)
        ]
        return out


ChillerPerformanceCalculator = ChillerPerformance

__all__ = ["ChillerPerformance", "ChillerPerformanceCalculator"]
