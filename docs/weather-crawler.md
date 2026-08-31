# 天氣爬蟲（ingestion.weather_crawler）

模組：`pygreenbuild.ingestion.weather_crawler.codis_crawler_tojson`  
匯入：

```python
from pygreenbuild import codis_yearly, codis_monthly, codis_daily
```

自中央氣象署 CODIS API 擷取測站年報／月報／日報觀測 JSON。預設寫入檔案；若需在程式中繼續處理，可設 `return_data=True` 取得 `list[dict]`（可再交給 [`json_to_dataframe`](json-to-dataframe.md)）。

---

## `codis_yearly`（年報）

### 用途

下載指定測站某一年的年報觀測資料。

### 輸入參數

| 參數 | 型別 | 單位 | 意義 |
|------|------|------|------|
| `station_id` | `str`（或可轉字串） | 不適用 | CWA 測站代號（例：臺北 `466920`） |
| `output_dir` | `str \| None` | 不適用 | JSON 輸出目錄。僅寫檔時必填；只要資料、不寫檔時可為 `None` |
| `year` | `int`／`str`（或可轉字串） | 年 | 西元年份（例：`2025`） |
| `return_data` | `bool` | 不適用 | `False`（預設）只寫檔並回傳成功與否與訊息；`True` 時回傳值多帶一筆資料。須以關鍵字傳入 |

### 回傳值

| 條件 | 型別 | 意義 |
|------|------|------|
| `return_data=False` | `tuple[bool, str]` | `(success, message)` |
| `return_data=True` | `tuple[bool, list[dict] \| None, str]` | `(success, data, message)`；失敗時 `data` 為 `None` |

有指定 `output_dir` 時，成功會寫出 `{year}_{station_id}.json`（例：`2025_466920.json`），與是否 `return_data` 無關。

### 使用範例

```python
from pygreenbuild import codis_yearly

ok, msg = codis_yearly("466920", "test_output", 2025)

ok, data, msg = codis_yearly("466920", None, 2025, return_data=True)

ok, data, msg = codis_yearly(
    "466920", "test_output", 2025, return_data=True
)
```

### 可能例外與失敗條件

以回傳值表達失敗，通常不拋例外。常見情況：未提供 `output_dir` 卻要寫檔、Cookie／網路錯誤、API 格式不符或內容為空。

### 使用限制與注意事項

- 測站類型依代號前綴自動判斷（`46`→局屬、`C0`／`C1`→自動站等）。
- 需能取得有效 CODIS Cookie（見同目錄 Cookie 管理）。

---

## `codis_monthly`（月報）

### 用途

下載指定測站某一個月的月報觀測資料。

### 輸入參數

| 參數 | 型別 | 單位 | 意義 |
|------|------|------|------|
| `station_id` | `str` | 不適用 | CWA 測站代號 |
| `output_dir` | `str \| None` | 不適用 | JSON 輸出目錄。僅寫檔時必填；只要資料、不寫檔時可為 `None` |
| `setYM` | `str` | 不適用 | 年月；支援 `YYYYMM`、`YYYY-MM`、`YYYY-MM-DD`（後者取其年月） |
| `return_data` | `bool` | 不適用 | 同 `codis_yearly`；預設 `False`，須以關鍵字傳入 |

### 回傳值

| 條件 | 型別 | 意義 |
|------|------|------|
| `return_data=False` | `tuple[bool, str]` | `(success, message)` |
| `return_data=True` | `tuple[bool, list[dict] \| None, str]` | `(success, data, message)`；失敗時 `data` 為 `None` |

有指定 `output_dir` 時寫出 `{YYYYMM}_{station_id}.json`（例：`202411_466920.json`）。

### 使用範例

```python
from pygreenbuild import codis_monthly

codis_monthly("466920", "test_output", "202411")
codis_monthly("466920", "test_output", "2024-11")
codis_monthly("466920", "test_output", "2024-11-01")

ok, data, msg = codis_monthly(
    "466920", None, "2024-11", return_data=True
)
```

### 可能例外與失敗條件

以回傳值表達失敗。`setYM` 格式錯誤時會在 `message` 提示可用格式；其餘同 `codis_yearly`。

### 使用限制與注意事項

- 區間為該月 1 日至月底；`YYYY-MM-DD` 只用來指定年月，不限於該日。

---

## `codis_daily`（日報／區間）

### 用途

下載單日或多日氣象日報資料。若傳入多個日期，會自動取最小與最大作為區間；間隔不得超過 31 天。

### 輸入參數

| 參數 | 型別 | 單位 | 意義 |
|------|------|------|------|
| `station_id` | `str` | 不適用 | CWA 測站代號 |
| `output_dir` | `str \| None` | 不適用 | JSON 輸出目錄。僅寫檔時必填；只要資料、不寫檔時可為 `None` |
| `*dates` | `str`（一個或多個） | 不適用 | 日期，格式 `YYYY-MM-DD`；至少一個 |
| `return_data` | `bool` | 不適用 | 同 `codis_yearly`；預設 `False`，須以關鍵字傳入 |

### 回傳值

| 條件 | 型別 | 意義 |
|------|------|------|
| `return_data=False` | `tuple[bool, str]` | `(success, message)` |
| `return_data=True` | `tuple[bool, list[dict] \| None, str]` | `(success, data, message)`；失敗時 `data` 為 `None` |

有指定 `output_dir` 時的檔名：

| 情況 | 檔名 |
|------|------|
| 單日（或起迄同一天） | `{YYYY-MM-DD}_{station_id}.json` |
| 多日區間 | `{start}~{end}_{station_id}.json` |

例：`2024-11-01_466920.json`、`2024-11-01~2024-11-30_466920.json`

### 使用範例

```python
from pygreenbuild import codis_daily
from pygreenbuild.transform import json_to_dataframe

codis_daily("466920", "test_output", "2024-11-01")
codis_daily("466920", "test_output", "2024-11-01", "2024-11-30")

ok, data, msg = codis_daily(
    "466920", None, "2024-11-01", "2024-11-07", return_data=True
)

ok, data, msg = codis_daily(
    "466920", "test_output", "2024-11-01", return_data=True
)
if ok and data is not None:
    df = json_to_dataframe(data)
```

### 可能例外與失敗條件

以回傳值表達失敗。常見情況：未提供日期、日期格式非 `YYYY-MM-DD`、多日間隔超過 31 天、未提供 `output_dir` 卻要寫檔，以及 Cookie／網路／API 錯誤。

### 使用限制與注意事項

- 多個日期會先排序，以最小日為起、最大日為迄；中間缺漏的日期參數不會改成「只下載列出的那幾天」。
- 單日請求時間範圍為當日 `00:00:00`～`23:59:59`。

---

## 鄉鎮天氣預報（CWA OpenData）

鄉鎮預報（`cwa_township_forecast_3day`／`cwa_township_forecast_week`）另篇說明，詳見 [鄉鎮天氣預報爬蟲](cwa-township-forecast.md)。兩者定位差異：

| 項目 | CODIS（`codis_*`） | 鄉鎮預報（`cwa_township_forecast_*`） |
|------|--------------------|--------------------------------------|
| 資料性質 | 測站**觀測**歷史資料 | 鄉鎮**預報**未來資料 |
| 認證 | 自動管理的 Session Cookie | CWA OpenData API 授權碼（`api_key` 參數） |
| 資料集 | CODIS station API | 逐縣市 `F-D0047-001`～`087` |
| 資料結構 | 觀測時序 `list[dict]` | `Locations` 巢狀 `list[dict]` |

> 預報 JSON 結構與 CODIS 觀測不同，**不能**直接餵給 [`json_to_dataframe`](json-to-dataframe.md)。

---

## 相關模組

同目錄尚有 Cookie 管理、CWA 測站清單、GreenBIM／ICDI API 下載與匯出等工具；天氣來源取得後，可再經 `parsers`／`transform` 進入標準化管線。詳見 [架構概覽](architecture.md)、[JSON 轉 DataFrame](json-to-dataframe.md)。
