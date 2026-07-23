# pygreenbuild

ICDI GreenBIM Python 工具：天氣資料擷取、WRF 預報相關流程，以及冰水主機成效（USRT／COP／EER）計算。

## 架構概覽

採 **ETL 管線**，另以 **metrics** 計算設備 KPI：

```
ingestion → parsers → transform → load
（擷取）    （解析）   （轉換）     （輸出）
                              ↘
                               metrics（成效／KPI）
```

| 層級 | 說明 |
|------|------|
| **ingestion** | 資料來源：天氣爬蟲、email、廠區／EMS DB |
| **parsers** | 原始格式解析 |
| **transform** | 欄位對應與正規化 |
| **load** | 輸出 CSV／資料庫 |
| **metrics** | 冷房需求 USRT、COP、EER、耗電率 |

使用說明見 [`docs/`](docs/)（Quarto `.qmd` 分篇），目錄規劃見 [`tree.csv`](tree.csv)。

## 開始使用

### 1. 虛擬環境
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / Mac
source .venv/bin/activate
```

### 2. 安裝
```bash
pip install git+https://github.com/Lucy-icdi/pygreenbuild.git
```

### 3. 天氣爬蟲（範例）
```python
from pygreenbuild import codis_yearly, codis_monthly, codis_daily

codis_yearly(station_id="466920", output_dir="test_output", year=2025)
codis_monthly(station_id="466920", output_dir="test_output", setDate="2024-11-01")
codis_daily("466920", "test_output", "2024-11-01", "2024-11-30")
```

### 4. 冰水主機成效（範例）

計算順序：流量 × |ΔT| → 冷房熱量 kW → 算 COP／EER → ×0.284 得 USRT → 算耗電率。

```python
from pygreenbuild.metrics import ChillerUSRTCalculator, ChillerPerformanceCalculator

# 原始冷房熱量 kW（kw_to_usrt=False；流量單位 CMH 會 ×16.7 轉 LPM）
cooling_kw = ChillerUSRTCalculator.calculate_single_chiller_usrt(
    flow_rate=17.49, flow_unit="CMH",
    return_temp=13.28, return_temp_unit="C",
    supply_temp=8.86, supply_temp_unit="C",
    kw_to_usrt=False,
)

# COP／EER（以原始熱量 kW 為輸入）
cop = ChillerPerformanceCalculator.calculate_cop(cooling_kw=cooling_kw, power_kw=643.95)
eer = ChillerPerformanceCalculator.calculate_eer(cooling_kw=cooling_kw, power_kw=643.95)  # kcal/h/W

# 耗電率：cooling_kw 與 usrt 擇一
rate = ChillerPerformanceCalculator.calculate_power_rate(
    power_kw=643.95, cooling_kw=cooling_kw
)  # 原始熱量 → 內部 ×0.284
rate = ChillerPerformanceCalculator.calculate_power_rate(
    power_kw=643.95, usrt=1149
)  # 已是 USRT → 不轉換

# DataFrame 批次：先算熱量 kW，再算成效
df = ChillerUSRTCalculator.calculate_usrts(
    df, flow_col="flow", return_temp_col="rwt", supply_temp_col="swt",
    kw_to_usrt=False, result_col="冷房熱量_kW",
)
df = ChillerPerformanceCalculator.calculate_performance(
    df, cooling_kw_col="冷房熱量_kW", power_cols=["CH_02", "CH_04"],
    power_rate_from="cooling_kw",  # 或 "usrt"（用已有／寫入的 USRT 欄）
)
# 結果多出：輸入功率_kW、COP、EER、USRT、耗電率
```

## 維護

```bash
pip install --upgrade git+https://github.com/Lucy-icdi/pygreenbuild.git
pip uninstall pygreenbuild
deactivate
```
