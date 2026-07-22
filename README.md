# pygreenbuild

ICDI GreenBIM Python 工具：天氣資料擷取、WRF 預報相關流程，以及冰水主機成效（USRT／COP）計算。

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
| **metrics** | 冷房需求 USRT、COP、耗電率 |

詳細說明見 [`doc/說明文件.md`](doc/說明文件.md)，目錄規劃見 [`tree.csv`](tree.csv)。

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
```python
from pygreenbuild.metrics import ChillerUSRTCalculator, ChillerPerformanceCalculator

# 冷房需求 USRT（流量單位 CMH 會 ×16.7 轉 LPM）
usrt = ChillerUSRTCalculator.calculate_single_chiller_usrt(
    flow_rate=17.49, flow_unit="CMH",
    return_temp=13.28, return_temp_unit="C",
    supply_temp=8.86, supply_temp_unit="C",
)

# COP／耗電率（需先有 USRT）
cop = ChillerPerformanceCalculator.calculate_cop(usrt=1149, power_kw=643.95)
rate = ChillerPerformanceCalculator.calculate_power_rate(usrt=1149, power_kw=643.95)
```

## 維護

```bash
pip install --upgrade git+https://github.com/Lucy-icdi/pygreenbuild.git
pip uninstall pygreenbuild
deactivate
```
