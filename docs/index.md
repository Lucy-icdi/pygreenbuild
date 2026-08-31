# 開始使用 pygreenbuild

`pygreenbuild` 是 ICDI GreenBIM 的 Python 工具套件，涵蓋：

- 天氣資料擷取（CODIS 年／月／日報、鄉鎮天氣預報 3 天／1 週）
- WRF 預報相關流程
- 熱舒適度計算（ISO 7730／ASHRAE 55 的 PMV／PPD）
- 冰水主機成效計算（USRT／COP／EER／耗電率）

本資料夾分篇說明套件用法。建議依下列順序閱讀：

| 篇章 | 內容 |
|------|------|
| [架構概覽](architecture.md) | ETL 與 metrics 層級定位 |
| [專案資料夾規劃](folder-structure.md) | 未來目標目錄樹與落地順序 |
| [天氣爬蟲](weather-crawler.md) | `codis_yearly`／`monthly`／`daily` |
| [鄉鎮天氣預報爬蟲](cwa-township-forecast.md) | `cwa_township_forecast_3day`／`week`，逐縣市批次下載 |
| [JSON 轉 DataFrame](json-to-dataframe.md) | CODIS 觀測 JSON → 中文欄位表 |
| [時間欄位轉換](transform-time.md) | 純日期／純時間／日期時間 |
| [時間缺口補齊](fill-time-gaps.md) | 依頻率插入缺失時間列並填值 |
| [資料庫／DataFrame 孤立 NA 填補](fill-table-na.md) | `fill_sql_table_na`／`fill_dataframe_na`／`apply_filled_na` |
| [PMV / PPD 舒適度](pmv.md) | ISO 7730 與 ASHRAE 55 的 PMV／PPD 計算 |
| [冷房需求 USRT](chiller-usrt.md) | 流量 × ΔT → 熱量 kW／USRT |
| [冰水主機成效](chiller-performance.md) | COP、EER、耗電率 |
| [MCP Server](mcp-server.md) | AI Agent 整合（FastMCP + stdio） |

## 安裝

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / Mac
source .venv/bin/activate

pip install git+https://github.com/Lucy-icdi/pygreenbuild.git
```

升級／解除安裝：

```bash
pip install --upgrade git+https://github.com/Lucy-icdi/pygreenbuild.git
pip uninstall pygreenbuild
```

## 快速範例

```python
from pygreenbuild import codis_daily, ChillerKPI
from pygreenbuild.metrics import calculatorUSRT
from pygreenbuild.transform import pmv_iso

# 天氣日報
codis_daily("466920", "test_output", "2024-11-01", "2024-11-30")

# ISO 7730 PMV／PPD 熱舒適度
comfort = pmv_iso(
    tdb=25.0,
    tr=25.0,
    vr=0.1,
    rh=50.0,
    met=1.2,
    clo=0.5,
)

# 冷房熱量 kW → COP／EER
cooling_kw = calculatorUSRT.calculate_single_chiller_usrt(
    flow_rate=17.49, flow_unit="CMH",
    return_temp=13.28, return_temp_unit="C",
    supply_temp=8.86, supply_temp_unit="C",
    kw_to_usrt=False,
)
cop = ChillerKPI.calculate_cop(cooling_kw=cooling_kw, power_kw=643.95)
eer = ChillerKPI.calculate_eer(cooling_kw=cooling_kw, power_kw=643.95)
```
