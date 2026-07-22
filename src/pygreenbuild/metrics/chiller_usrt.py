"""冷房需求 USRT（美制冷凍噸）計算。

核心流程：
1. 流量統一轉成 L/min
2. 溫度統一轉成 ℃
3. 熱量值 kW = Flow(L/min) × |ΔT|(℃) × 4.186 / 60
4. 若 kw_to_usrt=True（預設），再 × 0.284 得 USRT；若 False，回傳熱量值 kW
"""

from __future__ import annotations

import pandas as pd


class ChillerUSRT:
    """冷房需求（USRT）計算器。"""

    WATER_SPECIFIC_HEAT = 4.186  # kJ/(kg·℃)
    KW_TO_USRT_FACTOR = 0.284  # 1 kW ≈ 0.284 USRT（僅在 kw_to_usrt=True 時套用）

    # ------------------------------------------------------------------
    # 單位轉換
    # ------------------------------------------------------------------
    @staticmethod
    def _flow_to_lpm(flow: float, flow_unit: str) -> float:
        """各種流量單位 → L/min（係數對齊參考資料夾流量表）。"""
        unit = flow_unit.upper().strip()
        if unit in ("LPM", "L/MIN"):
            return flow
        if unit in ("LPS", "L/SEC", "L/S"):
            return flow * 60.0
        if unit in ("CMH", "M3/H", "M3/HR", "M³/H"):
            return flow * 16.7
        if unit in ("CMM", "M3/MIN", "M³/MIN"):
            return flow * 1000.0
        if unit in ("CFM", "FT3/MIN", "FT³/MIN"):
            return flow * 28.3
        if unit in ("GPM", "GAL/MIN"):
            return flow * 3.785
        raise ValueError(
            f"不支援的流量單位: {flow_unit!r}。請使用 LPM, LPS, CMH, CMM, CFM, GPM"
        )

    @staticmethod
    def _temp_to_celsius(temp: float, temp_unit: str) -> float:
        """溫度 → ℃。"""
        unit = temp_unit.upper().strip()
        if unit in ("C", "CELSIUS", "℃", "°C"):
            return temp
        if unit in ("F", "FAHRENHEIT", "℉", "°F"):
            return (temp - 32.0) * 5.0 / 9.0
        if unit in ("K", "KELVIN"):
            return temp - 273.15
        raise ValueError(f"不支援的溫度單位: {temp_unit!r}。請使用 C, F, K")

    # ------------------------------------------------------------------
    # 核心公式（已是 L/min + ℃）
    # ------------------------------------------------------------------
    @classmethod
    def _cooling_kw_from_lpm_c(
        cls, flow_lpm: float, return_temp_c: float, supply_temp_c: float
    ) -> float:
        """計算熱量值（kW）。"""
        delta_t = abs(return_temp_c - supply_temp_c)
        if flow_lpm <= 0 or delta_t <= 0:
            return 0.0
        return (flow_lpm * delta_t * cls.WATER_SPECIFIC_HEAT) / 60.0

    @classmethod
    def _apply_kw_to_usrt(cls, cooling_kw: float, kw_to_usrt: bool) -> float:
        """kw_to_usrt=True → USRT；False → 原熱量值 kW。"""
        if kw_to_usrt:
            return cooling_kw * cls.KW_TO_USRT_FACTOR
        return cooling_kw

    @classmethod
    def _from_lpm_c(
        cls,
        flow_lpm: float,
        return_temp_c: float,
        supply_temp_c: float,
        *,
        kw_to_usrt: bool = True,
    ) -> float:
        cooling_kw = cls._cooling_kw_from_lpm_c(flow_lpm, return_temp_c, supply_temp_c)
        return cls._apply_kw_to_usrt(cooling_kw, kw_to_usrt)

    # ------------------------------------------------------------------
    # 1. 單一台冰水主機
    # ------------------------------------------------------------------
    @classmethod
    def calculate_single_chiller_usrt(
        cls,
        flow_rate: float,
        flow_unit: str,
        return_temp: float,
        return_temp_unit: str,
        supply_temp: float,
        supply_temp_unit: str,
        kw_to_usrt: bool = True,
    ) -> float:
        """計算單一台冰水主機冷房需求。

        Parameters
        ----------
        kw_to_usrt :
            True（預設）：結果 × 0.284，回傳 USRT。
            False：不乘 0.284，回傳熱量值 kW。
        """
        flow_lpm = cls._flow_to_lpm(flow_rate, flow_unit)
        r_c = cls._temp_to_celsius(return_temp, return_temp_unit)
        s_c = cls._temp_to_celsius(supply_temp, supply_temp_unit)
        return cls._from_lpm_c(flow_lpm, r_c, s_c, kw_to_usrt=kw_to_usrt)

    @classmethod
    def single_chiller(
        cls,
        flow: float,
        return_temp: float,
        supply_temp: float,
        *,
        flow_unit: str = "CMH",
        temp_unit: str = "C",
        return_temp_unit: str | None = None,
        supply_temp_unit: str | None = None,
        kw_to_usrt: bool = True,
    ) -> float:
        """計算單一台冰水主機冷房需求（簡短介面）。"""
        return cls.calculate_single_chiller_usrt(
            flow_rate=flow,
            flow_unit=flow_unit,
            return_temp=return_temp,
            return_temp_unit=return_temp_unit or temp_unit,
            supply_temp=supply_temp,
            supply_temp_unit=supply_temp_unit or temp_unit,
            kw_to_usrt=kw_to_usrt,
        )

    # ------------------------------------------------------------------
    # 2. 聯合多個區域泵 → 總 USRT／總 kW
    # ------------------------------------------------------------------
    @classmethod
    def zone_pumps_total(
        cls, pumps: list[dict], *, kw_to_usrt: bool = True
    ) -> float:
        """聯合多個區域泵，先加總熱量值 kW。

        kw_to_usrt=True（預設）再 × 0.284 得總 USRT；False 回傳總 kW。
        """
        total_kw = 0.0
        for pump in pumps:
            flow_lpm = cls._flow_to_lpm(
                float(pump.get("flow", pump.get("flow_rate", 0))),
                str(pump.get("flow_unit", "CMH")),
            )
            temp_unit = str(pump.get("temp_unit", "C"))
            r_c = cls._temp_to_celsius(
                float(pump.get("return_temp", 0)),
                str(pump.get("return_temp_unit", temp_unit)),
            )
            s_c = cls._temp_to_celsius(
                float(pump.get("supply_temp", 0)),
                str(pump.get("supply_temp_unit", temp_unit)),
            )
            total_kw += cls._cooling_kw_from_lpm_c(flow_lpm, r_c, s_c)

        return cls._apply_kw_to_usrt(total_kw, kw_to_usrt)

    # ------------------------------------------------------------------
    # 3. 融冰 USRT
    # ------------------------------------------------------------------
    @classmethod
    def ice_melt(
        cls,
        flow: float,
        hex_return_temp: float,
        hex_supply_temp: float,
        *,
        flow_unit: str = "CFM",
        temp_unit: str = "C",
        return_temp_unit: str | None = None,
        supply_temp_unit: str | None = None,
        kw_to_usrt: bool = True,
    ) -> float:
        """計算融冰冷房需求。"""
        flow_lpm = cls._flow_to_lpm(abs(flow), flow_unit)
        r_c = cls._temp_to_celsius(
            hex_return_temp, return_temp_unit or temp_unit
        )
        s_c = cls._temp_to_celsius(
            hex_supply_temp, supply_temp_unit or temp_unit
        )
        return cls._from_lpm_c(flow_lpm, r_c, s_c, kw_to_usrt=kw_to_usrt)

    # ------------------------------------------------------------------
    # DataFrame 批次計算 USRT
    # ------------------------------------------------------------------
    @classmethod
    def calculate_usrts(
        cls,
        df: pd.DataFrame,
        *,
        flow_col: str,
        return_temp_col: str,
        supply_temp_col: str,
        flow_unit: str = "CMH",
        return_temp_unit: str = "C",
        supply_temp_unit: str = "C",
        result_col: str = "USRT",
        kw_to_usrt: bool = True,
    ) -> pd.DataFrame:
        """對 DataFrame 三欄逐列計算 USRT，結果併回原表。

        Parameters
        ----------
        flow_col :
            流量欄位名。
        return_temp_col :
            入水溫度欄位名（RWT）。
        supply_temp_col :
            出水溫度欄位名（SWT）。
        flow_unit :
            流量單位，預設 CMH（×16.7 → L/min）。
        return_temp_unit, supply_temp_unit :
            入／出水溫度單位。
        result_col :
            結果寫入欄位名。
        kw_to_usrt :
            True 回傳 USRT；False 回傳 kW。
        """
        out = df.copy()
        flow_lpm = out[flow_col].map(
            lambda v: cls._flow_to_lpm(float(v), flow_unit)
        )
        r_c = out[return_temp_col].map(
            lambda v: cls._temp_to_celsius(float(v), return_temp_unit)
        )
        s_c = out[supply_temp_col].map(
            lambda v: cls._temp_to_celsius(float(v), supply_temp_unit)
        )
        cooling_kw = (flow_lpm * (r_c - s_c).abs() * cls.WATER_SPECIFIC_HEAT) / 60.0
        cooling_kw = cooling_kw.where((flow_lpm > 0) & ((r_c - s_c).abs() > 0), 0.0)
        out[result_col] = cls._apply_kw_to_usrt(cooling_kw, kw_to_usrt)
        return out


ChillerUSRTCalculator = ChillerUSRT

__all__ = ["ChillerUSRT", "ChillerUSRTCalculator"]
