"""冰水主機成效計算：COP、EER、耗電率。

計算順序（由原始數據出發）::

    冷房熱量 (kW) = Flow(L/min) × |ΔT|(℃) × 4.186 / 60
                    （由 ``ChillerUSRT`` 以 kw_to_usrt=False 求出）
    COP           = 冷房熱量 (kW) / 輸入功率 (kW)
    EER (kcal/h/W)= 冷房熱量 (kW) × 0.86 / 主機耗電 (kW)
    USRT          = 冷房熱量 (kW) × 0.284
    耗電率        = 輸入功率 (kW) / USRT
                    （可傳 cooling_kw 自動 ×0.284，或直接傳已轉換的 usrt）
"""

from __future__ import annotations

import math

import pandas as pd

from .chiller_usrt import ChillerUSRT


class ChillerPerformance:
    """冰水主機 COP／EER／耗電率計算器。

    COP、EER 直接用原始熱量值（kW）；耗電率可選原始熱量或已轉換 USRT。
    """

    KW_TO_USRT_FACTOR = ChillerUSRT.KW_TO_USRT_FACTOR  # 0.284
    KW_TO_KCAL_H_FACTOR = 0.86  # EER：1 kW ≈ 0.86 kcal/h

    # ------------------------------------------------------------------
    # 1. COP（用原始熱量 kW）
    # ------------------------------------------------------------------
    @classmethod
    def calculate_cop(cls, cooling_kw: float, power_kw: float) -> float:
        """計算 COP（能效比）。

        COP = 冷房熱量(kW) / 輸入功率(kW)

        Parameters
        ----------
        cooling_kw :
            原始冷房熱量（kW），由 ``ChillerUSRT(..., kw_to_usrt=False)`` 求出。
        power_kw :
            冰機輸入功率合計（kW）。
        """
        if (
            cooling_kw <= 0
            or power_kw <= 0
            or math.isnan(cooling_kw)
            or math.isnan(power_kw)
        ):
            return float("nan")
        return cooling_kw / power_kw

    # ------------------------------------------------------------------
    # 2. EER（kcal/h/W，用原始熱量 kW）
    # ------------------------------------------------------------------
    @classmethod
    def calculate_eer(cls, cooling_kw: float, power_kw: float) -> float:
        """計算 EER（kcal/h/W）。

        EER = 冷房熱量(kW) × 0.86 / 主機耗電(kW)

        Parameters
        ----------
        cooling_kw :
            原始冷房熱量（kW）。
        power_kw :
            冰機輸入功率合計（kW）。
        """
        if (
            cooling_kw <= 0
            or power_kw <= 0
            or math.isnan(cooling_kw)
            or math.isnan(power_kw)
        ):
            return float("nan")
        return (cooling_kw * cls.KW_TO_KCAL_H_FACTOR) / power_kw

    # ------------------------------------------------------------------
    # 3. 耗電率（kW / USRT）
    # ------------------------------------------------------------------
    @classmethod
    def calculate_power_rate(
        cls,
        power_kw: float,
        *,
        cooling_kw: float | None = None,
        usrt: float | None = None,
    ) -> float:
        """計算耗電率（kW/USRT）。

        耗電率 = 輸入功率(kW) / USRT

        ``cooling_kw`` 與 ``usrt`` 擇一傳入：
        - ``cooling_kw``：原始熱量，內部 × 0.284 轉成 USRT
        - ``usrt``：已轉換過的 USRT，不再 × 0.284

        Parameters
        ----------
        power_kw :
            冰機輸入功率合計（kW）。
        cooling_kw :
            原始冷房熱量（kW）。與 ``usrt`` 互斥。
        usrt :
            已換算的冷房需求（USRT）。與 ``cooling_kw`` 互斥。
        """
        if (cooling_kw is None) == (usrt is None):
            raise ValueError("請擇一傳入 cooling_kw 或 usrt（不可同時給或同時省略）")

        if power_kw < 0 or math.isnan(power_kw):
            return float("nan")

        if cooling_kw is not None:
            if cooling_kw <= 0 or math.isnan(cooling_kw):
                return float("nan")
            capacity_usrt = cooling_kw * cls.KW_TO_USRT_FACTOR
        else:
            assert usrt is not None
            if usrt <= 0 or math.isnan(usrt):
                return float("nan")
            capacity_usrt = usrt

        return power_kw / capacity_usrt

    @classmethod
    def cooling_kw_to_usrt(cls, cooling_kw: float) -> float:
        """冷房熱量 (kW) → USRT（× 0.284）。"""
        if cooling_kw <= 0 or math.isnan(cooling_kw):
            return float("nan")
        return cooling_kw * cls.KW_TO_USRT_FACTOR

    # ------------------------------------------------------------------
    # 4. DataFrame 批次：先 COP／EER，再算耗電率
    # ------------------------------------------------------------------
    @classmethod
    def calculate_performance(
        cls,
        df: pd.DataFrame,
        *,
        cooling_kw_col: str = "冷房熱量_kW",
        power_cols: list[str] | str,
        cop_col: str = "COP",
        eer_col: str = "EER",
        power_rate_col: str = "耗電率",
        usrt_col: str | None = "USRT",
        power_rate_from: str = "cooling_kw",
        total_power_col: str | None = "輸入功率_kW",
    ) -> pd.DataFrame:
        """對 DataFrame 逐列計算 COP、EER、USRT、耗電率，結果併回原表。

        流程：以原始熱量 kW 算 COP／EER；耗電率可選以熱量或既有 USRT 計算。

        Parameters
        ----------
        df :
            需含冷房熱量 kW 欄（可由 ``ChillerUSRT.calculate_usrts(..., kw_to_usrt=False)``
            產出），以及一或多個功率欄（kW）。
        cooling_kw_col :
            原始冷房熱量（kW）欄位名。
        power_cols :
            功率欄位名，可為單一欄位字串或多欄 list（會加總）。
            例：``["CH_02", "CH_04", "CH_B01"]``。
        cop_col :
            COP 結果欄位名。
        eer_col :
            EER（kcal/h/W）結果欄位名。
        power_rate_col :
            耗電率結果欄位名。
        usrt_col :
            若給定，寫入 USRT（熱量 ×0.284）；設 ``None`` 則不輸出。
            當 ``power_rate_from="usrt"`` 時，以此欄（或既有同名欄）作為耗電率分母。
        power_rate_from :
            耗電率輸入來源：``"cooling_kw"``（×0.284）或 ``"usrt"``（不轉換）。
        total_power_col :
            若給定，寫入功率加總欄；設 ``None`` 則不輸出。
        """
        if power_rate_from not in ("cooling_kw", "usrt"):
            raise ValueError(
                f"power_rate_from 須為 'cooling_kw' 或 'usrt'，收到 {power_rate_from!r}"
            )

        out = df.copy()

        if isinstance(power_cols, str):
            power_cols = [power_cols]

        total_power = out[power_cols].sum(axis=1)
        if total_power_col is not None:
            out[total_power_col] = total_power

        cooling = out[cooling_kw_col]

        out[cop_col] = [
            cls.calculate_cop(float(q), float(p))
            for q, p in zip(cooling, total_power, strict=True)
        ]
        out[eer_col] = [
            cls.calculate_eer(float(q), float(p))
            for q, p in zip(cooling, total_power, strict=True)
        ]

        usrt_series = cooling.map(lambda q: cls.cooling_kw_to_usrt(float(q)))
        if usrt_col is not None:
            # cooling_kw 路徑：由熱量寫入／更新 USRT
            # usrt 路徑：保留既有 USRT；沒有才由熱量補上
            if power_rate_from == "cooling_kw" or usrt_col not in out.columns:
                out[usrt_col] = usrt_series

        if power_rate_from == "cooling_kw":
            out[power_rate_col] = [
                cls.calculate_power_rate(float(p), cooling_kw=float(q))
                for q, p in zip(cooling, total_power, strict=True)
            ]
        else:
            if usrt_col is None:
                raise ValueError(
                    "power_rate_from='usrt' 時須指定 usrt_col（不可為 None）"
                )
            out[power_rate_col] = [
                cls.calculate_power_rate(float(p), usrt=float(u))
                for u, p in zip(out[usrt_col], total_power, strict=True)
            ]
        return out


ChillerPerformanceCalculator = ChillerPerformance

__all__ = ["ChillerPerformance", "ChillerPerformanceCalculator"]
