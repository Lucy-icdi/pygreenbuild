# 架構概覽

`pygreenbuild` 採典型 **ETL 管線**（Extract → Transform → Load），以四個層級串接資料從「取得」到「輸出」；另以 **metrics** 層承載成效／KPI 計算，與 ETL 解耦。

## 資料流

```
ingestion → parsers → transform → load
（擷取）    （解析）   （轉換）     （輸出）
                              ↘
                               metrics
                              （成效／KPI 計算）
```

| 層級 | ETL 對應 | 定位 | 主要用途 |
|------|----------|------|----------|
| **ingestion** | Extract | 資料來源層 | 從外部把原始資料抓進來；只負責取得，不負責清洗。 |
| **parsers** | Extract / Parse | 格式解析層 | 將各來源原始格式解析成統一可處理的結構。 |
| **transform** | Transform | 轉換／正規化層 | 欄位對應、格式偵測與正規化，產出標準表格。 |
| **load** | Load | 輸出層 | 將結果寫出至 CSV、資料庫等目的地。 |
| **metrics** | （非 ETL） | 成效計算層 | 依公式計算設備／系統成效與 KPI（如冰水主機）。 |

規劃上可由管線腳本串起 **parser + transform + load**；成效計算可在標準資料產出後呼叫 **metrics**。

## 各層說明

### ingestion（資料來源層）

對接外部資料來源，將原始資料拉進系統。

- **weather_crawler**：氣象爬蟲（CODIS、Cookie、CWA 測站、GreenBIM／ICDI API）
- **email**：郵件來源讀取
- **ems_db**：廠區或 EMS 資料庫讀取（`fill_sql_table_na`：查表並填補孤立 NA，見 [fill-table-na.md](fill-table-na.md)）

原則：此層以取得資料為主；`fill_sql_table_na` 為讀取後的輕量填補，DataFrame 版見 transform。

### parsers（格式解析層）

將各來源原始內容解析成後續可處理的結構。

- `weather_parser.py`：天氣相關解析
- `excel_parser.py`：Excel 解析
- `factory_parser.py`：廠務／工廠來源解析（規劃）

### transform（轉換／正規化層）

對已解析資料做標準化，對齊欄位命名與資料品質規則。

- `mappings.py`、`detector.py`（規劃）
- `transform_time.py`：純日期／純時間／日期時間欄位轉換
- `fill_time_gaps.py`：依手動指定頻率補齊缺失時間列並填值
- `fill_dataframe_na.py`：回傳已填補的新 DataFrame（見 [fill-table-na.md](fill-table-na.md)）
- `json_to_dataframe.py`：CODIS 觀測 JSON → 中文欄位 DataFrame（見 [json-to-dataframe.md](json-to-dataframe.md)）
- `pmv.py`：ISO 7730／ASHRAE 55 的 PMV／PPD 舒適度計算（見 [pmv.md](pmv.md)）

### load（輸出層）

將轉換完成的資料寫到 CSV、資料庫等目的地（與來源解耦）。

- `codis_data_merge.py`：合併 CODIS 日／時／月資料
- `apply_filled_na.py`：將 `fill_sql_table_na` 填補結果 UPDATE 回資料庫或匯出 SQL（見 [fill-table-na.md](fill-table-na.md)）

### metrics（成效計算層）

承接已標準化的運轉資料，依領域公式計算成效與 KPI。不負責抓取、解析、欄位對應或寫檔。

| 模組 | Class | 用途 |
|------|-------|------|
| `chiller_usrt.py` | `calculatorUSRT` | 冷房需求 USRT（含融冰、區域泵） |
| `chiller_performance.py` | `ChillerPerformance` / `ChillerKPI`（`from pygreenbuild import ChillerKPI`） | COP、EER、耗電率 |

詳見 [冷房需求 USRT](chiller-usrt.md)、[冰水主機成效](chiller-performance.md)。

## 目錄對照（摘要）

```
src/pygreenbuild/
├─ ingestion/          # 資料來源層
│  ├─ weather_crawler/
│  ├─ email/
│  └─ ems_db/
├─ parsers/            # 格式解析層
├─ transform/          # 轉換／正規化層
│  └─ pmv.py           # PMV／PPD 舒適度
├─ load/               # 輸出層
└─ metrics/            # 成效計算層
   ├─ chiller_usrt.py
   └─ chiller_performance.py
```

> 後續還規劃 `features`、`models`、`api`、`config`、`utils`、`scripts/`、`data/` 等。完整目標目錄樹、狀態標記與落地順序見 [專案資料夾規劃](folder-structure.md)。
