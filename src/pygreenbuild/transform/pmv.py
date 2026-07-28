"""ISO 7730 與 ASHRAE 55 的 PMV/PPD 舒適度計算。

公開 API
--------
pmv_iso(...)
pmv_ashrae(...)

本模組僅使用 Python 標準庫。輸入可為純量，或等長序列（list／tuple）；
純量回傳單一字典，向量化輸入回傳字典列表。

演算對齊 pythermalcomfort（Fanger PMV／Gagge two-node SET／Cooling Effect）：
https://github.com/pythermalcomfort/pythermalcomfort
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any, Literal

__all__ = ["pmv_iso", "pmv_ashrae"]

_MET_TO_W_M2 = 58.15
_STILL_AIR_THRESHOLD = 0.1
_BODY_SURFACE_AREA = 1.8258
_P_ATM = 101325.0
_SBC = 5.6697e-8

IsoOutput = Literal["all", "pmv", "ppd", "tsv", "standard"]
AshraeOutput = Literal[
    "all",
    "pmv",
    "ppd",
    "tsv",
    "standard",
    "cooling_effect",
    "compliance",
]
_ISO_OUTPUT_KEYS: frozenset[str] = frozenset(
    {"all", "pmv", "ppd", "tsv", "standard"}
)
_ASHRAE_OUTPUT_KEYS: frozenset[str] = frozenset(
    {"all", "pmv", "ppd", "tsv", "standard", "cooling_effect", "compliance"}
)

# 熱感分類上界（不含上界本身，對齊 pythermalcomfort mapping(..., right=False)）
_TSV = (
    (-2.5, "Cold"),
    (-1.5, "Cool"),
    (-0.5, "Slightly Cool"),
    (0.5, "Neutral"),
    (1.5, "Slightly Warm"),
    (2.5, "Warm"),
    (math.inf, "Hot"),
)


def _is_vector(value: Any) -> bool:
    """判斷是否為可向量化的序列（排除字串／位元組）。"""
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _broadcast(*values: Any) -> list[tuple[float, ...]]:
    """將純量與序列廣播成等長列資料。"""
    lengths = [len(v) for v in values if _is_vector(v)]
    if not lengths:
        return [tuple(float(v) for v in values)]
    size = max(lengths)
    if any(length not in (1, size) for length in lengths):
        raise ValueError("所有陣列輸入的長度必須相同，或長度為 1。")

    rows: list[tuple[float, ...]] = []
    for i in range(size):
        row: list[float] = []
        for value in values:
            if _is_vector(value):
                item = value[0] if len(value) == 1 else value[i]
            else:
                item = value
            row.append(float(item))
        rows.append(tuple(row))
    return rows


def _validate(tdb: float, tr: float, vr: float, rh: float, met: float, clo: float, wme: float) -> None:
    """驗證單一組 PMV 輸入的基本物理合理性。"""
    vals = (tdb, tr, vr, rh, met, clo, wme)
    if not all(math.isfinite(v) for v in vals):
        raise ValueError("所有輸入都必須是有限數值。")
    if vr < 0:
        raise ValueError("vr 不可小於 0 m/s。")
    if not 0 <= rh <= 100:
        raise ValueError("rh 必須介於 0 到 100%。")
    if met <= 0:
        raise ValueError("met 必須大於 0。")
    if clo < 0:
        raise ValueError("clo 不可小於 0。")
    if wme < 0 or wme >= met:
        raise ValueError("wme 必須大於等於 0，且小於 met。")


def _thermal_sensation(pmv: float) -> str:
    """依 PMV 對應熱感分類標籤。"""
    for upper, label in _TSV:
        if pmv < upper:
            return label
    return "Hot"


def _fanger_pmv(
    tdb: float,
    tr: float,
    vr: float,
    rh: float,
    met: float,
    clo: float,
    wme: float = 0.0,
) -> float:
    """Fanger PMV（ISO 7730 Annex D 數值演算法）。"""
    pa = rh * 10.0 * math.exp(16.6536 - 4030.183 / (tdb + 235.0))
    icl = 0.155 * clo
    m = met * _MET_TO_W_M2
    w = wme * _MET_TO_W_M2
    mw = m - w

    if icl <= 0.078:
        f_cl = 1.0 + 1.29 * icl
    else:
        f_cl = 1.05 + 0.645 * icl

    hcf = 12.1 * math.sqrt(vr)
    taa = tdb + 273.0
    tra = tr + 273.0
    # ISO 7730:2025 Annex D 衣著表面溫度初值
    t_cla = taa + (35.5 - tdb) / (3.5 * (6.45 * icl + 0.1))
    p1 = icl * f_cl
    p2 = p1 * 3.96
    p3 = p1 * 100.0
    p4 = p1 * taa
    p5 = 308.7 - 0.028 * mw + p2 * (tra / 100.0) ** 4
    xn = t_cla / 100.0
    xf = t_cla / 50.0
    eps = 0.00015

    n = 0
    while abs(xn - xf) > eps:
        xf = (xf + xn) / 2.0
        hcn = 2.38 * abs(100.0 * xf - taa) ** 0.25
        hc = max(hcf, hcn)
        xn = (p5 + p4 * hc - p2 * xf**4) / (100.0 + p3 * hc)
        n += 1
        if n > 150:
            raise RuntimeError("PMV 衣著表面溫度迭代未收斂。")

    tcl = 100.0 * xn - 273.0
    hl1 = 3.05 * 0.001 * (5733.0 - 6.99 * mw - pa)
    hl2 = 0.42 * (mw - _MET_TO_W_M2) if mw > _MET_TO_W_M2 else 0.0
    hl3 = 1.7e-5 * m * (5867.0 - pa)
    hl4 = 0.0014 * m * (34.0 - tdb)
    hl5 = 3.96 * f_cl * (xn**4 - (tra / 100.0) ** 4)
    hl6 = f_cl * hc * (tcl - tdb)
    ts = 0.303 * math.exp(-0.036 * m) + 0.028
    return ts * (mw - hl1 - hl2 - hl3 - hl4 - hl5 - hl6)


def _ppd(pmv: float) -> float:
    """由 PMV 計算 PPD（%）。"""
    return 100.0 - 95.0 * math.exp(-0.03353 * pmv**4 - 0.2179 * pmv**2)


def _sat_vapor_pressure_torr(tdb: float) -> float:
    """飽和水氣壓（torr）。"""
    return math.exp(18.6686 - 4030.183 / (tdb + 235.0))


def _set_core(
    tdb: float,
    tr: float,
    v: float,
    rh: float,
    met: float,
    clo: float,
    wme: float = 0.0,
    *,
    p_atm: float = _P_ATM,
    body_surface_area: float = _BODY_SURFACE_AREA,
    calculate_ce: bool = True,
) -> float:
    """Gagge two-node 標準有效溫度（SET）。

    ``calculate_ce=True`` 時對齊 ASHRAE Cooling Effect 路徑
   （站姿、略過代謝率對對流係數的加成）。
    """
    vapor_pressure = rh * _sat_vapor_pressure_torr(tdb) / 100.0
    air_speed = max(v, _STILL_AIR_THRESHOLD)
    k_clo = 0.25
    body_weight = 70.0
    met_factor = 58.2
    c_sw = 170.0
    c_dil = 120.0
    c_str = 0.5
    max_skin_blood_flow = 90.0
    max_sweating = 500.0

    temp_skin_neutral = 33.7
    temp_core_neutral = 36.8
    alpha = 0.1
    temp_body_neutral = alpha * temp_skin_neutral + (1.0 - alpha) * temp_core_neutral
    skin_blood_flow_neutral = 6.3

    t_skin = temp_skin_neutral
    t_core = temp_core_neutral
    m_bl = skin_blood_flow_neutral
    e_skin = 0.1 * met
    q_sensible = 0.0
    w = 0.0

    pressure_in_atmospheres = p_atm / 101325.0
    r_clo = 0.155 * clo
    f_a_cl = 1.0 + 0.15 * clo
    lr = 2.2 / pressure_in_atmospheres
    rm = (met - wme) * met_factor
    m = met * met_factor

    i_cl = 0.45 if clo > 0 else 1.0
    if clo > 0:
        w_max = 0.59 * air_speed**-0.08
    else:
        w_max = 0.38 * air_speed**-0.29

    h_cc = 3.0 * pressure_in_atmospheres**0.53
    h_fc = 8.600001 * (air_speed * pressure_in_atmospheres) ** 0.53
    h_cc = max(h_cc, h_fc)
    if not calculate_ce and met > 0.85:
        h_cc = max(h_cc, 5.66 * (met - 0.85) ** 0.39)

    h_r = 4.7
    h_t = h_r + h_cc
    r_a = 1.0 / (f_a_cl * h_t)
    t_op = (h_r * tr + h_cc * tdb) / h_t

    q_res = 0.0023 * m * (44.0 - vapor_pressure)
    c_res = 0.0014 * m * (34.0 - tdb)

    # 對齊上游：n 從 1 起跳，實際模擬 59 步
    n_simulation = 1
    while n_simulation < 60:
        n_simulation += 1

        t_cl = (r_a * t_skin + r_clo * t_op) / (r_a + r_clo)
        for _ in range(150):
            # 站姿：衣著發射率 0.95、有效輻射面積比 0.73
            h_r = 4.0 * 0.95 * _SBC * (((t_cl + tr) / 2.0) + 273.15) ** 3 * 0.73
            h_t = h_r + h_cc
            r_a = 1.0 / (f_a_cl * h_t)
            t_op = (h_r * tr + h_cc * tdb) / h_t
            t_cl_new = (r_a * t_skin + r_clo * t_op) / (r_a + r_clo)
            if abs(t_cl_new - t_cl) <= 0.01:
                t_cl = t_cl_new
                break
            t_cl = t_cl_new
        else:
            raise RuntimeError("SET 衣著表面溫度迭代未收斂。")

        q_sensible = (t_skin - t_op) / (r_a + r_clo)
        # 核心↔皮膚熱傳遞（組織傳導 + 血流）
        hf_cs = (t_core - t_skin) * (5.28 + 1.163 * m_bl)
        s_core = m - hf_cs - q_res - c_res - wme
        s_skin = hf_cs - q_sensible - e_skin
        tc_sk = 0.97 * alpha * body_weight
        tc_cr = 0.97 * (1.0 - alpha) * body_weight
        t_skin += (s_skin * body_surface_area) / (tc_sk * 60.0)
        t_core += (s_core * body_surface_area) / (tc_cr * 60.0)
        t_body = alpha * t_skin + (1.0 - alpha) * t_core

        sk_sig = t_skin - temp_skin_neutral
        warm_sk = max(sk_sig, 0.0)
        cold_sk = max(-sk_sig, 0.0)
        cr_sig = t_core - temp_core_neutral
        warm_cr = max(cr_sig, 0.0)
        cold_cr = max(-cr_sig, 0.0)
        bd_sig = t_body - temp_body_neutral
        warm_b = max(bd_sig, 0.0)

        m_bl = (skin_blood_flow_neutral + c_dil * warm_cr) / (1.0 + c_str * cold_sk)
        m_bl = min(max(m_bl, 0.5), max_skin_blood_flow)
        m_rsw = min(c_sw * warm_b * math.exp(warm_sk / 10.7), max_sweating)
        e_rsw = 0.68 * m_rsw

        r_ea = 1.0 / (lr * f_a_cl * h_cc)
        r_ecl = r_clo / (lr * i_cl)
        e_max = (_sat_vapor_pressure_torr(t_skin) - vapor_pressure) / (r_ea + r_ecl)
        if e_max == 0.0:
            e_max = 0.001
        p_rsw = e_rsw / e_max
        w = 0.06 + 0.94 * p_rsw
        e_diff = w * e_max - e_rsw
        if w > w_max:
            w = w_max
            p_rsw = w_max / 0.94
            e_rsw = p_rsw * e_max
            e_diff = 0.06 * (1.0 - p_rsw) * e_max
        if e_max < 0.0:
            e_diff = 0.0
            e_rsw = 0.0
            w = w_max
        e_skin = e_rsw + e_diff

        met_shivering = 19.4 * cold_sk * cold_cr
        m = rm + met_shivering
        alpha = 0.0417737 + 0.7451833 / (m_bl + 0.585417)

    q_skin = q_sensible + e_skin
    p_s_sk = _sat_vapor_pressure_torr(t_skin)

    # 標準環境（用於反推 SET）
    h_r_s = h_r
    h_c_s = 3.0 * pressure_in_atmospheres**0.53
    if not calculate_ce and met > 0.85:
        h_c_s = max(h_c_s, 5.66 * (met - 0.85) ** 0.39)
    h_c_s = max(h_c_s, 3.0)
    h_t_s = h_c_s + h_r_s
    r_clo_s = 1.52 / ((met - wme / met_factor) + 0.6944) - 0.1835
    r_cl_s = 0.155 * r_clo_s
    f_a_cl_s = 1.0 + k_clo * r_clo_s
    f_cl_s = 1.0 / (1.0 + 0.155 * f_a_cl_s * h_t_s * r_clo_s)
    i_m_s = 0.45
    i_cl_s = (
        i_m_s
        * h_c_s
        / h_t_s
        * (1.0 - f_cl_s)
        / (h_c_s / h_t_s - f_cl_s * i_m_s)
    )
    r_a_s = 1.0 / (f_a_cl_s * h_t_s)
    r_ea_s = 1.0 / (lr * f_a_cl_s * h_c_s)
    r_ecl_s = r_cl_s / (lr * i_cl_s)
    h_d_s = 1.0 / (r_a_s + r_cl_s)
    h_e_s = 1.0 / (r_ea_s + r_ecl_s)

    delta = 0.0001
    set_old = round(t_skin - q_skin / h_d_s, 2)
    dx = 100.0
    n_set = 0
    while abs(dx) > 0.01:
        err_1 = (
            q_skin
            - h_d_s * (t_skin - set_old)
            - w * h_e_s * (p_s_sk - 0.5 * _sat_vapor_pressure_torr(set_old))
        )
        err_2 = (
            q_skin
            - h_d_s * (t_skin - (set_old + delta))
            - w
            * h_e_s
            * (p_s_sk - 0.5 * _sat_vapor_pressure_torr(set_old + delta))
        )
        denom = err_2 - err_1
        if abs(denom) < 1e-12:
            break
        set_new = set_old - delta * err_1 / denom
        dx = set_new - set_old
        set_old = set_new
        n_set += 1
        if n_set > 200:
            break
    return set_old


def _cooling_effect(
    tdb: float,
    tr: float,
    vr: float,
    rh: float,
    met: float,
    clo: float,
    wme: float,
) -> float:
    """ASHRAE 55 Cooling Effect（°C）。

    定義：自 ``tdb`` 與 ``tr`` 各減去相同 CE 後，在靜風（0.1 m/s）下的 SET
    等於原高風速條件的 SET。
    """
    if vr <= _STILL_AIR_THRESHOLD:
        return 0.0

    target = _set_core(tdb, tr, vr, rh, met, clo, wme, calculate_ce=True)

    def residual(ce: float) -> float:
        return (
            _set_core(
                tdb - ce,
                tr - ce,
                _STILL_AIR_THRESHOLD,
                rh,
                met,
                clo,
                wme,
                calculate_ce=True,
            )
            - target
        )

    low, high = 0.0, 40.0
    f_low, f_high = residual(low), residual(high)
    if f_low == 0.0:
        return 0.0
    if f_low * f_high > 0:
        # 無根：對齊上游 brentq 失敗時回傳 0
        return 0.0

    for _ in range(80):
        mid = (low + high) / 2.0
        f_mid = residual(mid)
        if abs(f_mid) < 1e-4 or high - low < 1e-4:
            return mid
        if f_low * f_mid <= 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid
    return (low + high) / 2.0


def _one_result(
    pmv: float,
    *,
    standard: str,
    cooling_effect: float | None = None,
    round_output: bool = True,
) -> dict[str, Any]:
    """組裝單一條件的輸出字典。"""
    ppd = _ppd(pmv)
    result: dict[str, Any] = {
        "pmv": round(pmv, 2) if round_output else pmv,
        "ppd": round(ppd, 1) if round_output else ppd,
        "tsv": _thermal_sensation(pmv),
        "standard": standard,
    }
    if standard == "ASHRAE 55-2023":
        ce = 0.0 if cooling_effect is None else cooling_effect
        result["cooling_effect"] = round(ce, 2) if round_output else ce
        result["compliance"] = -0.5 < pmv < 0.5
    return result


def _collapse(results: list[dict[str, Any]]) -> dict[str, Any] | list[dict[str, Any]]:
    """純量輸入壓成單一字典，否則回傳列表。"""
    return results[0] if len(results) == 1 else results


def _select_output(
    results: list[dict[str, Any]],
    output: str,
    allowed: frozenset[str],
) -> Any:
    """依 ``output`` 回傳完整結果或單一欄位值。"""
    if output not in allowed:
        raise ValueError(
            f"output 須為 {sorted(allowed)} 之一，收到 {output!r}"
        )
    if output == "all":
        return _collapse(results)
    values = [item[output] for item in results]
    return values[0] if len(values) == 1 else values


def pmv_iso(
    tdb: float | Sequence[float],
    tr: float | Sequence[float],
    vr: float | Sequence[float],
    rh: float | Sequence[float],
    met: float | Sequence[float],
    clo: float | Sequence[float],
    wme: float | Sequence[float] = 0.0,
    *,
    round_output: bool = True,
    output: IsoOutput = "all",
) -> Any:
    """計算 ISO 7730:2025 的 PMV／PPD。

    Parameters
    ----------
    tdb :
        空氣乾球溫度，單位 °C。
    tr :
        平均輻射溫度，單位 °C。
    vr :
        相對風速，單位 m/s（含活動引起之相對風速）。
    rh :
        相對濕度，單位 %。
    met :
        代謝率，單位 met。
    clo :
        衣著基本隔熱值，單位 clo。
    wme :
        外部做功，單位 met；預設 0。
    round_output :
        若為 True，PMV 四捨五入至小數 2 位、PPD 至小數 1 位。
    output :
        回傳內容。``"all"`` 回傳完整字典；``"pmv"``／``"ppd"``／``"tsv"``／
        ``"standard"`` 只回傳該欄位，方便寫入 DataFrame。

    Returns
    -------
    Any
        ``output="all"``：純量回傳字典，向量化回傳字典列表。
        其他 ``output``：純量回傳該欄位值，向量化回傳該欄位值列表。

    Raises
    ------
    ValueError
        輸入非有限數、``vr``/``rh``/``met``/``clo``/``wme`` 超出合理範圍、
        序列長度不一致，或 ``output`` 不合法。
    RuntimeError
        衣著表面溫度迭代未收斂。
    """
    results: list[dict[str, Any]] = []
    for row in _broadcast(tdb, tr, vr, rh, met, clo, wme):
        _validate(*row)
        pmv = _fanger_pmv(*row)
        results.append(
            _one_result(pmv, standard="ISO 7730:2025", round_output=round_output)
        )
    return _select_output(results, output, _ISO_OUTPUT_KEYS)


def pmv_ashrae(
    tdb: float | Sequence[float],
    tr: float | Sequence[float],
    vr: float | Sequence[float],
    rh: float | Sequence[float],
    met: float | Sequence[float],
    clo: float | Sequence[float],
    wme: float | Sequence[float] = 0.0,
    *,
    round_output: bool = True,
    output: AshraeOutput = "all",
) -> Any:
    """計算 ASHRAE 55-2023 的 PMV／PPD（含 Cooling Effect）。

    當 ``vr > 0.1`` m/s 時，先以 Gagge SET 求 Cooling Effect（CE），
    再以 ``tdb-CE``、``tr-CE``、靜風 0.1 m/s 代入 Fanger PMV。

    Parameters
    ----------
    tdb, tr, vr, rh, met, clo, wme :
        意義與單位同 :func:`pmv_iso`。
    round_output :
        若為 True，數值結果四捨五入。
    output :
        回傳內容。``"all"`` 回傳完整字典；亦可指定 ``"pmv"``、``"ppd"``、
        ``"tsv"``、``"standard"``、``"cooling_effect"``、``"compliance"``。

    Returns
    -------
    Any
        ``output="all"``：純量回傳字典，向量化回傳字典列表。
        其他 ``output``：純量回傳該欄位值，向量化回傳該欄位值列表。

    Raises
    ------
    ValueError
        同 :func:`pmv_iso`，或 ``output`` 不合法。
    RuntimeError
        PMV 或 SET 迭代未收斂。
    """
    results: list[dict[str, Any]] = []
    for row in _broadcast(tdb, tr, vr, rh, met, clo, wme):
        _validate(*row)
        ta, mrt, air_speed, humidity, activity, clothing, work = row
        ce = _cooling_effect(ta, mrt, air_speed, humidity, activity, clothing, work)
        pmv = _fanger_pmv(
            ta - ce,
            mrt - ce,
            _STILL_AIR_THRESHOLD if ce > 0 else air_speed,
            humidity,
            activity,
            clothing,
            work,
        )
        results.append(
            _one_result(
                pmv,
                standard="ASHRAE 55-2023",
                cooling_effect=ce,
                round_output=round_output,
            )
        )
    return _select_output(results, output, _ASHRAE_OUTPUT_KEYS)
