# JSON 轉 DataFrame（transform.json_to_dataframe）

模組：`pygreenbuild.transform.json_to_dataframe`  
匯入：

```python
from pygreenbuild.transform import json_to_dataframe
```

將中央氣象署（CWA）CODIS 觀測 JSON（`list` of `dict`）轉成中文欄位的 `pandas.DataFrame`，並套用缺測清理與觀測時間進位規則。

---

## `json_to_dataframe`

### 用途

把爬蟲或檔案讀入的 CODIS JSON 正規化成表格：

1. 以 `pandas.json_normalize` 扁平化巢狀欄位
2. 依對應表抽出中文欄名（小時／日／月自動偵測，或手動指定）
3. 調整 `觀測時間` 為 `23:59:00`–`23:59:59` 的紀錄（改為隔天 `00:00:00`）
4. 清理缺測代碼與不合理數值
5. 將 `NaN`／`None` 統一為系統遺失值 `pd.NA`（顯示為 `<NA>`）
6. 刪除整欄皆為空值的欄位

常用於 `codis_merge` 等合併流程的前置轉換。

### 輸入參數

| 參數 | 型別 | 單位 | 意義 |
|------|------|------|------|
| `data` | `Sequence[Mapping[str, Any]]` | 不適用 | 觀測紀錄列表；每筆為 dict（可巢狀） |
| `column_mapping` | `Mapping[str, str \| None] \| None` | 不適用 | 中文欄名 → JSON 扁平路徑；`None`（預設）自動偵測。路徑為 `None` 時該欄恒為空，最終會被刪除 |

#### 自動格式偵測（`column_mapping=None`）

依**第一筆**資料的鍵判斷：

| 鍵 | 格式 | 對應表 |
|----|------|--------|
| `DataTime` | 小時報 | `_CWA_HOUR_MAPPING` |
| `DataDate` | 日報 | `_CWA_DAY_MAPPING` |
| `DataYearMonth` | 月報 | `_CWA_MONTH_MAPPING` |

### 回傳值

| 型別 | 單位 | 意義 |
|------|------|------|
| `pd.DataFrame` | 依欄位而定 | 中文欄位觀測表（已去掉整欄空白欄）。若有 `觀測時間`，格式為字串 `YYYY-MM-DDTHH:MM:SS`；缺測統一為 `pd.NA`（`<NA>`） |

主要輸出欄位依格式而定（節錄）：

| 格式 | 時間欄 | 常見氣象欄（例） |
|------|--------|------------------|
| 小時 | `觀測時間` | `氣溫`、`相對溼度`、`風速`、`降水量`… |
| 日 | `觀測時間` | `氣溫`、`最高氣溫`、`最低氣溫`、`降水量`… |
| 月 | `觀測月份` | `氣溫`、`降水量`、`降水日數`… |

### 使用範例

```python
from pygreenbuild.transform import json_to_dataframe

# 小時報（巢狀 JSON；會被 json_normalize 扁平化）
hour_data = [
    {
        "DataTime": "2025-08-15T14:00:00",
        "AirTemperature": {"Instantaneous": 28.5},
        "RelativeHumidity": {"Instantaneous": 70},
        "Precipitation": {"Accumulation": 0.0},
    },
    {
        "DataTime": "2025-08-15T23:59:00",
        "AirTemperature": {"Instantaneous": 26.0},
        "RelativeHumidity": {"Instantaneous": 80},
        "Precipitation": {"Accumulation": "T"},
    },
]
df_hour = json_to_dataframe(hour_data)
# df_hour["觀測時間"].iloc[1] → "2025-08-16T00:00:00"（23:59 進位）
# df_hour["降水量"].iloc[1] → 0.4（微量降水 T）

# 日報
day_data = [
    {
        "DataDate": "2025-08-15",
        "AirTemperature": {"Mean": 27.0, "Maximum": 32.0, "Minimum": 24.0},
    }
]
df_day = json_to_dataframe(day_data)

# 月報
month_data = [
    {
        "DataYearMonth": "2025-08",
        "AirTemperature": {"Mean": 28.0},
        "Precipitation": {"Accumulation": 120.5},
    }
]
df_month = json_to_dataframe(month_data)

# 自訂欄位對應
df_custom = json_to_dataframe(
    hour_data,
    column_mapping={
        "觀測時間": "DataTime",
        "氣溫": "AirTemperature.Instantaneous",
    },
)
```

### 可能例外

| 例外 | 條件 |
|------|------|
| `ValueError` | `data` 為空（`[]`） |
| `ValueError` | 未提供 `column_mapping`，且第一筆資料不含 `DataTime`／`DataDate`／`DataYearMonth` |

### 使用限制與注意事項

- **輸入必須是 list**；單筆 dict 請包成 `[record]`。巢狀路徑經 `json_normalize` 後以點號連接（如 `AirTemperature.Instantaneous`）。
- 對應表中路徑為 `None` 的欄位（如小時報的 `濕球溫度`、`雲冪高`）、JSON 缺少的路徑，以及清理後整欄皆空的欄位，最終都會從結果刪除。
- 若某欄僅部分列為空、其餘有值，該欄會保留，空值列維持 `pd.NA`。
- **缺測表示**：浮點 `nan`（`numpy.nan`）與 pandas `<NA>`（`pd.NA`）並非同一物件；本函式會統一成 `pd.NA`。
- **觀測時間進位**：`23:59:00`–`23:59:59` 一律改為隔天 `00:00:00`（與 `to_datetime_column` 同一規則）；結果寫回字串。
- **降水量**：字串 `"T"`（微量）改為數值 `0.4`（單位：mm）。
- **缺測代碼**：空字串、`NULL`／`null`／`NaN`、`-99`／`-999` 系列、`x`、`&`、`V`、`/`、`--` 等改為 `pd.NA`。
- **數值遮罩**（時間類欄位略過）：
  - 溫度相關欄（氣溫、露點、地溫等）：數值 `< -50` → `pd.NA`
  - 其餘非時間欄：數值 `< 0` → `pd.NA`
- 時間類欄位定義：`觀測時間`、`觀測月份`，或欄名以「時間」結尾者。
- R 端請 `source("scripts/python_functions.R")` 後呼叫 `json_to_dataframe`；包裝函式會以 `py_to_r` 轉成 R `data.frame`，才可用 `head()`／`View()`／`dplyr`。若直接 `import(...)$json_to_dataframe`，回傳值仍是 Python `pandas.DataFrame`，請自行 `reticulate::py_to_r(...)` 再轉成 `data.frame`。

```r
library(reticulate)
source("scripts/python_functions.R")

dt <- codis_daily("C2C480", NULL, "2026-05-01", "2026-05-31", return_data = TRUE)[[2]]
DT <- json_to_dataframe(dt)  # 已是 R data.frame
head(DT)
```
