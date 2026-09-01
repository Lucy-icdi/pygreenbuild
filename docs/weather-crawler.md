# 天氣爬蟲（ingestion.weather_crawler）

模組：`pygreenbuild.ingestion.weather_crawler.codis_stn_obs_crawler`  
匯入：

```python
from pygreenbuild import (
    codis_yearly,
    codis_monthly,
    codis_daily,
    codis_single_hourly_monthly,
    codis_single_daily_yearly,
    codis_single_monthly_yearly,
)
```

自中央氣象署 CODIS API 擷取測站年報／月報／日報／單項逐時月報表／單項逐日年報表／單項逐月年報表觀測 JSON。預設寫入檔案；若需在程式中繼續處理，可設 `return_data=True` 取得 `list[dict]`（可再交給 [`json_to_dataframe`](json-to-dataframe.md)）。

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

ok, msg = codis_yearly(
    station_id="466920",
    output_dir="test_output",
    year=2025,
)

ok, data, msg = codis_yearly(
    station_id="466920",
    output_dir=None,
    year=2025,
    return_data=True,
)

ok, data, msg = codis_yearly(
    station_id="466920",
    output_dir="test_output",
    year=2025,
    return_data=True,
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

ok, msg = codis_monthly(
    station_id="466920",
    output_dir="test_output",
    setYM="202411",
)
ok, msg = codis_monthly(
    station_id="466920",
    output_dir="test_output",
    setYM="2024-11",
)
ok, msg = codis_monthly(
    station_id="466920",
    output_dir="test_output",
    setYM="2024-11-01",
)

ok, data, msg = codis_monthly(
    station_id="466920",
    output_dir=None,
    setYM="2024-11",
    return_data=True,
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

# *dates 為可變位置參數，無法用關鍵字傳入，須接在 station_id、output_dir 之後
ok, msg = codis_daily(
    "466920",          # station_id
    "test_output",     # output_dir
    "2024-11-01",      # *dates（單日）
)
ok, msg = codis_daily(
    "466920",          # station_id
    "test_output",     # output_dir
    "2024-11-01",      # *dates 起日
    "2024-11-30",      # *dates 迄日
)

ok, data, msg = codis_daily(
    "466920",          # station_id
    None,              # output_dir：不寫檔
    "2024-11-01",
    "2024-11-07",
    return_data=True,
)

ok, data, msg = codis_daily(
    "466920",          # station_id
    "test_output",     # output_dir
    "2024-11-01",
    return_data=True,
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

## `codis_single_hourly_monthly`（單項逐時月報表）

模組：`pygreenbuild.ingestion.weather_crawler.codis_single_item_crawler`

### 用途

下載指定測站某一個月的**單項**逐時觀測資料（CODIS「單項逐時月報表」，API `type=one_date`）。與 `codis_monthly` 的完整月報不同，此函式只抓一個觀測要素。

### 輸入參數

| 參數 | 型別 | 單位 | 意義 |
|------|------|------|------|
| `station_id` | `str` | 不適用 | CWA 測站代號（例：淡水 `466900`） |
| `setYM` | `str` | 不適用 | 年月；支援 `YYYYMM`、`YYYY-MM`、`YYYY-MM-DD`（後者取其年月） |
| `item` | `str` | 不適用 | 觀測要素。可傳對照表中文 key（正則模糊比對）、英文 value，或直接傳 API 代碼 |
| `match_index` | `int \| None` | 不適用 | 多個 key 匹配時選用第幾個（從 1 起算）。預設 `None`，等同第 1 個 |
| `return_data` | `str \| None` | 不適用 | JSON 輸出目錄。未填則不寫檔，只回傳 Python 物件 |

### `item` 解析規則

1. 與對照表 **value** 完全相符（不分大小寫）→ 直接使用該英文代碼，例如 `SeaLevelPressure`。
2. 與對照表 **key** 完全相符 → 使用對應 value，例如 `海平面氣壓(hPa)`。
3. 將輸入視為**正則表達式**，對 key 做模糊比對。多筆匹配時用 `match_index` 選第幾個；未填則取第 1 筆。
4. 仍無匹配、且輸入本身是 API 代碼格式（英數字、可含逗號）→ 原樣送給 API。

單項逐時月報表可用要素：

| 中文 key | API value |
|----------|-----------|
| 測站氣壓(hPa) | `StationPressure` |
| 海平面氣壓(hPa) | `SeaLevelPressure` |
| 氣溫(℃) | `AirTemperature` |
| 露點溫度(℃) | `DewPointTemperature` |
| 相對溼度(%) | `RelativeHumidity` |
| 風速(m/s) / 風向(360degree) | `WindSpeed,WindDirection` |
| 最大瞬間風(m/s) / 最大瞬間風風向(360degree) | `PeakGust` |
| 降水量(mm) | `Precipitation` |
| 降水時數(hour) | `PrecipitationDuration` |
| 日照時數(hour) | `SunshineDuration` |
| 全天空日射量(MJ/㎡) | `GlobalSolarRadiation` |
| 能見度(km) | `Visibility` |
| 能見度_自動(km) | `VisibilityAuto` |
| 紫外線指數 | `UVIndex` |
| 總雲量(0~10) | `TotalCloudAmount` |
| 總雲量_衛星(0~10) | `TotalCloudAmountSat` |
| 地溫0cm～地溫100cm | `SoilTemperatureAt0cm` 等 |

### 回傳值

| 型別 | 單位 | 意義 |
|------|------|------|
| `tuple[bool, list[dict] \| None, str]` | 不適用 | `(success, data, message)`；失敗時 `data` 為 `None` |

有指定 `return_data`（輸出目錄）時，另外寫出 `{YYYYMM}_{station_id}_{item}.json`（例：`202603_466900_SeaLevelPressure.json`）。`WindSpeed,WindDirection` 的逗號會改成底線。未填 `return_data` 則不寫檔。

每筆 `dts` 通常為 `{DateTime, <ItemName>: {Instantaneous, Instantaneousf}}`。

### 使用範例

```python
from pygreenbuild import codis_single_hourly_monthly

# 中文模糊比對「氣壓」：預設取第 1 個「測站氣壓(hPa)」
ok, data, msg = codis_single_hourly_monthly(
    station_id="466900",
    setYM="2026-02",
    item="氣壓",
    return_data="test_output",
)

# 「能見度」會匹配「能見度(km)」與「能見度_自動(km)」；match_index=2 取後者
ok, data, msg = codis_single_hourly_monthly(
    station_id="466900",
    setYM="2026-02",
    item="能見度",
    match_index=2,
    return_data="test_output",
)

# 英文 API 代碼；未填 return_data 則不寫檔，只回傳 Python 物件
ok, data, msg = codis_single_hourly_monthly(
    station_id="466900",
    setYM="2026-02",
    item="SeaLevelPressure",
)

# 多個「氣壓」匹配時選第 2 個「海平面氣壓(hPa)」
ok, data, msg = codis_single_hourly_monthly(
    station_id="466900",
    setYM="2026-02",
    item="氣壓",
    match_index=2,
)
```

### 可能例外與失敗條件

以回傳值表達失敗，通常不拋例外。常見情況：

- `item` 無法對到任何要素，或正則語法無效
- `match_index` 小於 1，或大於匹配筆數（訊息會列出可選項目）
- `setYM` 格式錯誤
- Cookie／網路錯誤、API 格式不符或內容為空

### 使用限制與注意事項

- 區間為該月 1 日 `00:00:00` 至月底 `23:59:59`。
- 測站類型依代號前綴自動判斷（同 `codis_monthly`）。
- 需能取得有效 CODIS Cookie。

---

## `codis_single_daily_yearly`（單項逐日年報表）

模組：`pygreenbuild.ingestion.weather_crawler.codis_single_item_crawler`

### 用途

下載指定測站某一年的**單項**逐日觀測資料（CODIS「單項逐日年報表」，API `type=one_month`）。與 `codis_yearly` 的完整年報不同，此函式只抓一個觀測要素。

### 輸入參數

| 參數 | 型別 | 單位 | 意義 |
|------|------|------|------|
| `station_id` | `str` | 不適用 | CWA 測站代號（例：竹子湖 `466930`） |
| `year` | `int \| str` | 年 | 年份；支援 `YYYY`、`YYYYMM`、`YYYY-MM`、`YYYY-MM-DD`（後者取其年） |
| `item` | `str` | 不適用 | 觀測要素。可傳對照表中文 key（正則模糊比對）、英文 value，或直接傳 API 代碼 |
| `match_index` | `int \| None` | 不適用 | 多個 key 匹配時選用第幾個（從 1 起算）。預設 `None`，等同第 1 個 |
| `return_data` | `str \| None` | 不適用 | JSON 輸出目錄。未填則不寫檔，只回傳 Python 物件 |

`item` 解析規則與 `codis_single_hourly_monthly` 相同，但使用單項逐日年報表對照表（含最高／最低氣溫、最小相對溼度、日照率等年報才有的要素）。

單項逐日年報表可用要素（節錄）：

| 中文 key | API value |
|----------|-----------|
| 測站氣壓(hPa) | `StationPressure` |
| 海平面氣壓(hPa) | `SeaLevelPressure` |
| 測站最高氣壓(hPa) / 測站最高氣壓時間(LST) | `MaxStationPressure` |
| 測站最低氣壓(hPa) / 測站最低氣壓時間(LST) | `MinStationPressure` |
| 氣溫(℃) | `AirTemperature` |
| 最高氣溫(℃) / 最高氣溫時間(LST) | `MaxAirTemperature` |
| 最低氣溫(℃) / 最低氣溫時間(LST) | `MinAirTemperature` |
| 相對溼度(%) | `RelativeHumidity` |
| 最小相對溼度(%) / 最小相對溼度時間(LST) | `MinRelativeHumidity` |
| 降水量(mm) | `Precipitation` |
| 日照率(%) | `SunshineDurationRate` |
| A型蒸發量(mm) | `EvaporationClassAPan` |
| 日最高紫外線指數 / 日最高紫外線指數時間(LST) | `MaxUVIndex` |

完整清單見模組常數 `ONE_MONTH_ITEMS`。

### 回傳值

| 型別 | 單位 | 意義 |
|------|------|------|
| `tuple[bool, list[dict] \| None, str]` | 不適用 | `(success, data, message)`；失敗時 `data` 為 `None` |

有指定 `return_data`（輸出目錄）時，另外寫出 `{YYYY}_{station_id}_{item}.json`（例：`2026_466930_SeaLevelPressure.json`）。未填 `return_data` 則不寫檔。

### 使用範例

```python
from pygreenbuild import codis_single_daily_yearly

# 英文 API 代碼；未填 return_data 則不寫檔
ok, data, msg = codis_single_daily_yearly(
    station_id="466930",
    year=2026,
    item="SeaLevelPressure",
)

# 中文模糊比對「氣壓」：預設取第 1 個「測站氣壓(hPa)」
ok, data, msg = codis_single_daily_yearly(
    station_id="466930",
    year="2026",
    item="氣壓",
    return_data="test_output",
)

# 多個「氣壓」匹配時選第 2 個「海平面氣壓(hPa)」
ok, data, msg = codis_single_daily_yearly(
    station_id="466930",
    year="2026",
    item="氣壓",
    match_index=2,
)
```

### 可能例外與失敗條件

以回傳值表達失敗，通常不拋例外。常見情況：

- `item` 無法對到任何要素，或正則語法無效
- `match_index` 小於 1，或大於匹配筆數（訊息會列出可選項目）
- `year` 格式錯誤
- Cookie／網路錯誤、API 格式不符或內容為空

### 使用限制與注意事項

- 區間為該年 1 月 1 日 `00:00:00` 至 12 月 31 日 `00:00:00`（與 CODIS 網站請求一致）。
- 測站類型依代號前綴自動判斷（同 `codis_yearly`）。
- 需能取得有效 CODIS Cookie。

---

## `codis_single_monthly_yearly`（單項逐月年報表）

模組：`pygreenbuild.ingestion.weather_crawler.codis_single_item_crawler`

### 用途

下載指定測站某一年的**單項**逐月觀測資料（CODIS「單項逐月年報表」，API `type=one_year`）。與 `codis_yearly` 的完整年報不同，此函式只抓一個觀測要素。

### 輸入參數

| 參數 | 型別 | 單位 | 意義 |
|------|------|------|------|
| `station_id` | `str` | 不適用 | CWA 測站代號（例：竹子湖 `466930`） |
| `year` | `int \| str` | 年 | 年份；支援 `YYYY`、`YYYYMM`、`YYYY-MM`、`YYYY-MM-DD`（後者取其年） |
| `item` | `str` | 不適用 | 觀測要素。可傳對照表中文 key（正則模糊比對）、英文 value，或直接傳 API 代碼 |
| `match_index` | `int \| None` | 不適用 | 多個 key 匹配時選用第幾個（從 1 起算）。預設 `None`，等同第 1 個 |
| `return_data` | `str \| None` | 不適用 | JSON 輸出目錄。未填則不寫檔，只回傳 Python 物件 |

`item` 解析規則與 `codis_single_hourly_monthly` 相同，但使用單項逐月年報表對照表（含降水日數、最大日降雨量、平均日最高紫外線指數等）。

單項逐月年報表可用要素（節錄）：

| 中文 key | API value |
|----------|-----------|
| 測站氣壓(hPa) | `StationPressure` |
| 海平面氣壓(hPa) | `SeaLevelPressure` |
| 氣溫(℃) | `AirTemperature` |
| 最高氣溫(℃) / 最高氣溫時間(LST) | `MaxAirTemperature` |
| 降水量(mm) | `Precipitation` |
| 降水日數(day) | `PrecipitationDays` |
| 最大日降雨量(mm)/最大日降雨量時間(LST) | `MaxDailyPrecipitation` |
| 相對溼度(%) | `RelativeHumidity` |
| A型蒸發量(mm) | `EvaporationClassAPan` |
| 平均日最高紫外線指數 | `MaxMeanUVIndex` |

完整清單見模組常數 `ONE_YEAR_ITEMS`。

### 回傳值

| 型別 | 單位 | 意義 |
|------|------|------|
| `tuple[bool, list[dict] \| None, str]` | 不適用 | `(success, data, message)`；失敗時 `data` 為 `None` |

有指定 `return_data`（輸出目錄）時，另外寫出 `{YYYY}_{station_id}_{item}_monthly.json`（例：`2026_466930_StationPressure_monthly.json`）。未填 `return_data` 則不寫檔。檔名加 `_monthly` 以免與單項逐日年報表撞名。

### 使用範例

```python
from pygreenbuild import codis_single_monthly_yearly

# 英文 API 代碼；未填 return_data 則不寫檔
ok, data, msg = codis_single_monthly_yearly(
    station_id="466930",
    year=2026,
    item="StationPressure",
)

# 中文模糊比對「氣壓」：預設取第 1 個「測站氣壓(hPa)」
ok, data, msg = codis_single_monthly_yearly(
    station_id="466930",
    year="2026",
    item="氣壓",
    return_data="test_output",
)

# 多個「氣壓」匹配時選第 2 個「海平面氣壓(hPa)」
ok, data, msg = codis_single_monthly_yearly(
    station_id="466930",
    year="2026",
    item="氣壓",
    match_index=2,
)
```

### 可能例外與失敗條件

以回傳值表達失敗，通常不拋例外。常見情況：

- `item` 無法對到任何要素，或正則語法無效
- `match_index` 小於 1，或大於匹配筆數（訊息會列出可選項目）
- `year` 格式錯誤
- Cookie／網路錯誤、API 格式不符或內容為空

### 使用限制與注意事項

- 區間為該年 1 月 1 日 `00:00:00` 至 12 月 31 日 `00:00:00`。
- CODIS 網頁介面常以測站開始觀測日作為 `start`，一次列出歷年列；本函式只請求指定年。
- 測站類型依代號前綴自動判斷（同 `codis_yearly`）。
- 需能取得有效 CODIS Cookie。

---

## 鄉鎮天氣預報（CWA OpenData）

鄉鎮預報（`cwa_township_forecast_3day`／`cwa_township_forecast_week`）另篇說明，詳見 [鄉鎮天氣預報爬蟲](cwa-township-forecast.md)。兩者定位差異：
|------|--------------------|--------------------------------------|
| 資料性質 | 測站**觀測**歷史資料 | 鄉鎮**預報**未來資料 |
| 認證 | 自動管理的 Session Cookie | CWA OpenData API 授權碼（`api_key` 參數） |
| 資料集 | CODIS station API | 逐縣市 `F-D0047-001`～`087` |
| 資料結構 | 觀測時序 `list[dict]` | `Locations` 巢狀 `list[dict]` |

> 預報 JSON 結構與 CODIS 觀測不同，**不能**直接餵給 [`json_to_dataframe`](json-to-dataframe.md)。

---

## 相關模組

同目錄尚有 Cookie 管理、CWA 測站清單、GreenBIM／ICDI API 下載與匯出等工具；天氣來源取得後，可再經 `parsers`／`transform` 進入標準化管線。詳見 [架構概覽](architecture.md)、[JSON 轉 DataFrame](json-to-dataframe.md)。
