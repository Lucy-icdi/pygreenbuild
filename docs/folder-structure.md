# 專案資料夾規劃

本文描述 `pygreenbuild` **未來目標目錄結構**，作為模組擴充與重構的對照基準。層級定位見 [架構概覽](architecture.md)。

狀態標記：

| 標記 | 意義 |
|------|------|
| （既有） | 目前 `src/` 已存在對應模組 |
| （規劃） | 尚未落地或僅部分存在 |
| （升級） | 既有模組，規劃中調整角色或補齊檔案 |

---

## 目標目錄樹

```
src/pygreenbuild/
│
├─ ingestion/                         # 資料來源層（Extract）
│   ├─ weather_crawler/               # （既有／升級）氣象擷取
│   │   ├─ codis_cookie_manager.py
│   │   ├─ codis_crawler_tojson.py
│   │   ├─ cwa_stations_crawler.py
│   │   ├─ greenbim_api_export.py
│   │   ├─ icdi_api_download.py
│   │   └─ __init__.py
│   │
│   ├─ email/                         # （既有）郵件來源
│   │   ├─ email_reader.py
│   │   └─ __init__.py
│   │
│   ├─ ems_db/                        # （既有）廠區／EMS 資料庫
│   │   ├─ factory_db.py
│   │   └─ __init__.py
│   │
│   └─ __init__.py
│
├─ parsers/                           # （既有／升級）格式解析層
│   ├─ weather_parser.py
│   ├─ excel_parser.py
│   ├─ factory_parser.py              # （規劃）
│   └─ __init__.py
│
├─ transform/                         # （既有／升級）轉換／正規化層
│   ├─ mappings.py                    # （規劃）
│   ├─ detector.py                    # （規劃）
│   ├─ transform_time.py              # （既有）日期／時間／日期時間欄位轉換
│   ├─ fill_time_gaps.py              # （既有）依頻率補齊缺失時間列
│   ├─ json_to_dataframe.py           # （既有）
│   └─ __init__.py
│
├─ load/                              # （既有／升級）輸出層
│   ├─ to_csv.py                      # （規劃）
│   ├─ to_database.py                 # （規劃）
│   ├─ codis_data_merge.py            # （既有）
│   └─ __init__.py
│
├─ metrics/                           # （既有）成效／KPI 計算層
│   ├─ chiller_usrt.py
│   ├─ chiller_performance.py
│   └─ __init__.py
│
├─ features/                          # （規劃）特徵工程／ML 前處理
│   ├─ merge_data.py
│   ├─ feature_engineering.py
│   └─ __init__.py
│
├─ models/                            # （規劃）模型訓練與推論
│   ├─ train.py
│   ├─ predict.py
│   └─ __init__.py
│
├─ api/                               # （規劃）服務介面
│   ├─ main.py
│   ├─ schemas.py
│   └─ __init__.py
│
├─ config/                            # （規劃）設定集中管理
│   ├─ settings.py
│   └─ __init__.py
│
├─ utils/                             # （規劃）共用工具
│   ├─ logger.py
│   ├─ time_utils.py
│   └─ __init__.py
│
└─ __init__.py
```

倉庫根目錄另規劃：

```
scripts/                              # （規劃）可執行入口腳本
├─ run_weather_ingestion.py
├─ run_email_ingestion.py
├─ run_pipeline.py                    # parser + transform + load
├─ run_feature.py
├─ run_training.py
└─ run_api.py

data/                                 # （規劃）本機資料工作區（通常不納入版本庫）
├─ sample/
├─ temp/
└─ metadata/
```

---

## 各區塊角色

### `src/pygreenbuild/ingestion/`

對接外部來源，只負責「取得原始資料」，不做欄位清洗或業務轉換。

| 子目錄 | 狀態 | 說明 |
|--------|------|------|
| `weather_crawler/` | 既有 | CODIS、Cookie、CWA 測站、GreenBIM／ICDI API |
| `email/` | 既有 | 郵件讀取 |
| `ems_db/` | 既有 | 廠區或 EMS 資料庫讀取（檔名 `factory_db.py`） |

### `src/pygreenbuild/parsers/`

將各來源原始格式解析成後續可處理的統一結構。

### `src/pygreenbuild/transform/`

欄位對應、格式偵測與正規化，產出標準表格。規劃補齊 `mappings`／`detector`；時間欄位轉換見既有 `transform_time`；時間缺口補齊見既有 `fill_time_gaps`。

### `src/pygreenbuild/load/`

將結果寫出至 CSV、資料庫等目的地。既有 `codis_data_merge.py`；規劃泛用 `to_csv`／`to_database`。

### `src/pygreenbuild/metrics/`

依領域公式計算設備／系統成效與 KPI（如 USRT、COP）。與 ETL 解耦，詳見 [架構概覽](architecture.md)。

### `src/pygreenbuild/features/`、`models/`

ML 相關：資料合併、特徵工程，以及訓練／推論。在標準資料與成效計算穩定後擴充。

### `src/pygreenbuild/api/`、`config/`、`utils/`

對外 API、集中設定與共用工具（日誌、時間處理等）。

### `scripts/`

對外執行入口，串接 ingestion、pipeline、feature、training、API，避免在套件內寫死 CLI 流程。

### `data/`

本機樣本、暫存與中繼資料目錄；建議以 `.gitignore` 排除實際資料檔，僅保留目錄結構或範例說明。

---

## 建議落地順序

1. **補齊 ETL 核心**：`parsers.factory_parser`、`transform`（mappings／detector）、`load`（to_csv／to_database）
2. **統一設定與工具**：`config/`、`utils/`
3. **管線腳本**：`scripts/run_pipeline.py` 等入口
4. **特徵與模型**：`features/` → `models/`
5. **服務介面**：`api/`

---

## 與現況命名對照

早期草稿曾使用 `ingestion/weather/`、`ingestion/factory/` 等名稱。現行與文件統一為：

| 草稿名稱 | 現行／目標名稱 |
|----------|----------------|
| `ingestion/weather/` | `ingestion/weather_crawler/` |
| `ingestion/factory/` | `ingestion/ems_db/` |
| （未列） | `metrics/`（成效計算，已納入架構） |

擴充新模組時，請同步更新本文與 [架構概覽](architecture.md)。
