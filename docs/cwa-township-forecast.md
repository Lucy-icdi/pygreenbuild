# 鄉鎮天氣預報爬蟲（ingestion.weather_crawler）

模組：`pygreenbuild.ingestion.weather_crawler.cwa_township_forecast`
匯入：

```python
from pygreenbuild import cwa_township_forecast_3day, cwa_township_forecast_week
```

自中央氣象署（CWA）OpenData 擷取 368 個鄉鎮市區的天氣預報 JSON。預設批次下載全部 22 個縣市，每個縣市寫出一個 JSON 檔；也可以只指定其中幾個縣市。

與 CODIS 觀測資料不同，本模組需要 **CWA OpenData API 授權碼**（免費會員申請）。

---

## 授權碼設定

授權碼由第一個參數 `api_key` 傳入，格式為 `CWA-` 開頭的字串，例如 `"CWA-F8F425DD-****"`（`*` 為實際授權碼的其餘字元）。

```python
ok, msg = cwa_township_forecast_3day("CWA-F8F425DD-****", "D:/database/districtfc")
```

授權碼寫進版本庫時，請在呼叫端自行管理，例如以 `python-dotenv` 讀取 `.env`：

```python
import os
from dotenv import load_dotenv

load_dotenv()
ok, msg = cwa_township_forecast_3day(os.environ["CWA_API_KEY"], "D:/database/districtfc")
```

---

## `cwa_township_forecast_3day`（未來 3 天）

### 用途

下載鄉鎮天氣預報－未來 3 天（逐 3 小時），包含溫度、露點溫度、體感溫度、相對濕度、風向、風速、降雨機率、舒適度指數、天氣現象等 11 項氣象因子。

### 輸入參數

| 參數 | 型別 | 單位 | 意義 |
|------|------|------|------|
| `api_key` | `str` | 不適用 | CWA OpenData 授權碼，例：`"CWA-F8F425DD-****"`。必填，空字串或 `None` 會直接回報失敗 |
| `output_dir` | `str \| None` | 不適用 | JSON 輸出目錄，由使用者自行決定。`return_data=False` 時必填；只要資料、不寫檔時可為 `None` |
| `*counties` | `str`（零個或多個） | 不適用 | 縣市名稱（例：`"臺北市"`）或資料編號（例：`"F-D0047-061"`）。**不指定則批次下載全部 22 個縣市** |
| `return_data` | `bool` | 不適用 | `False`（預設）只寫檔並回傳成功與否與訊息；`True` 時回傳值多帶一筆資料。須以關鍵字傳入 |

### 回傳值

| 條件 | 型別 | 意義 |
|------|------|------|
| `return_data=False` | `tuple[bool, str]` | `(success, message)` |
| `return_data=True` | `tuple[bool, list[dict] \| None, str]` | `(success, data, message)` |

- `success`：只要有任一縣市下載失敗即為 `False`，失敗的縣市與原因會列在 `message`。
- `data`：各縣市 `records.Locations` 內容串接而成的清單，每個元素對應一個縣市；**完全沒取得任何資料時**才是 `None`。
- 檔名格式為 `{今日日期}_township_3day_{縣市}.json`，例：`2026-08-26_township_3day_臺北市.json`。

### 使用範例

```python
from pygreenbuild import cwa_township_forecast_3day

API_KEY = "CWA-F8F425DD-****"  # 換成自己的 CWA OpenData 授權碼

# 批次下載全部 22 個縣市，各寫出一個 JSON
ok, msg = cwa_township_forecast_3day(API_KEY, "D:/database/districtfc")

# 只下載臺北市（以縣市名稱指定）
ok, msg = cwa_township_forecast_3day(API_KEY, "D:/database/districtfc", "臺北市")

# 以資料編號指定，只取回資料不寫檔（output_dir 傳 None）
ok, data, msg = cwa_township_forecast_3day(
    API_KEY, None, "F-D0047-061", return_data=True
)

# 一次指定多個縣市
ok, msg = cwa_township_forecast_3day(
    API_KEY, "D:/database/districtfc", "臺北市", "新北市", "宜蘭縣"
)
```

### 可能例外與失敗條件

以回傳值表達失敗，通常不拋例外。常見情況：

| 情況 | `message` 關鍵字 |
|------|------------------|
| `return_data=False` 但未給 `output_dir` | `匯出 JSON 模式需提供 output_dir` |
| `api_key` 為 `None`、空字串或全空白 | `缺少 CWA API 授權碼` |
| 縣市名稱或資料編號無法辨識 | `無法識別的縣市別或資料編號` |
| 傳入空字串／空白 | `縣市別或資料編號不可為空白` |
| 授權碼錯誤或過期 | `授權失敗（401）` |
| 網路中斷、逾時 | `發生網路錯誤` |
| 回應非 JSON | `伺服器回應格式錯誤` |
| API 回傳結構不符 | `API 回傳格式不符預期` |

縣市解析失敗會在送出任何請求前就中止，不會產生半套輸出。

### 使用限制與注意事項

- `api_key` 與 `output_dir` 都是位置參數，不能省略。只要資料不寫檔時，`output_dir` 傳 `None` 並加上 `return_data=True`。
- 授權碼前後空白會自動去除。
- 縣市名稱支援「台／臺」兩種寫法（`"台北市"` 會自動視為 `"臺北市"`），前後空白會自動去除。
- 資料編號**只用來辨識縣市**。把 1 週的編號（如 `F-D0047-083`）傳給本函式，下載的仍是該縣市（連江縣）的未來 3 天資料集。編號大小寫與 `-`／`_` 皆可（`f_d0047_061` 等同 `F-D0047-061`）。
- 重複指定同一縣市只會下載一次。
- 預設模式會連續送出 22 個請求，請避免高頻率呼叫。
- 單一縣市失敗不會中斷其餘縣市，成功的縣市仍會寫檔。

---

## `cwa_township_forecast_week`（未來 1 週）

### 用途

下載鄉鎮天氣預報－未來 1 週（逐 12 小時），包含平均／最高／最低溫度、平均相對濕度、體感溫度、舒適度指數、12 小時降雨機率、風向、最大風速、紫外線指數、天氣現象等 15 項氣象因子。

### 輸入參數

與 `cwa_township_forecast_3day` 完全相同，差別僅在對應的資料編號。

### 回傳值

與 `cwa_township_forecast_3day` 相同。檔名格式為 `{今日日期}_township_week_{縣市}.json`，例：`2026-08-26_township_week_連江縣.json`。

### 使用範例

```python
from pygreenbuild import cwa_township_forecast_week

API_KEY = "CWA-F8F425DD-****"  # 換成自己的 CWA OpenData 授權碼

# 批次下載全部 22 個縣市
ok, msg = cwa_township_forecast_week(API_KEY, "D:/database/districtfc7day")

# 只下載連江縣（以 1 週的資料編號指定）
ok, msg = cwa_township_forecast_week(
    API_KEY, "D:/database/districtfc7day", "F-D0047-083"
)

# 取回資料接續處理（output_dir 傳 None 代表不寫檔）
ok, data, msg = cwa_township_forecast_week(API_KEY, None, "臺中市", return_data=True)
if ok and data is not None:
    for county_block in data:
        print(county_block["LocationsName"], len(county_block["Location"]))
```

### 可能例外與失敗條件

與 `cwa_township_forecast_3day` 相同。

### 使用限制與注意事項

與 `cwa_township_forecast_3day` 相同。

---

## 縣市與資料編號對照

模組常數 `COUNTY_DATASET_IDS` 記錄下列對照，值為 `(未來 3 天, 未來 1 週)`。

| 縣市 | 未來 3 天 | 未來 1 週 | 鄉鎮數 |
|------|-----------|-----------|--------|
| 宜蘭縣 | F-D0047-001 | F-D0047-003 | 12 |
| 桃園市 | F-D0047-005 | F-D0047-007 | 13 |
| 新竹縣 | F-D0047-009 | F-D0047-011 | 13 |
| 苗栗縣 | F-D0047-013 | F-D0047-015 | 18 |
| 彰化縣 | F-D0047-017 | F-D0047-019 | 26 |
| 南投縣 | F-D0047-021 | F-D0047-023 | 13 |
| 雲林縣 | F-D0047-025 | F-D0047-027 | 20 |
| 嘉義縣 | F-D0047-029 | F-D0047-031 | 18 |
| 屏東縣 | F-D0047-033 | F-D0047-035 | 33 |
| 臺東縣 | F-D0047-037 | F-D0047-039 | 16 |
| 花蓮縣 | F-D0047-041 | F-D0047-043 | 13 |
| 澎湖縣 | F-D0047-045 | F-D0047-047 | 6 |
| 基隆市 | F-D0047-049 | F-D0047-051 | 7 |
| 新竹市 | F-D0047-053 | F-D0047-055 | 3 |
| 嘉義市 | F-D0047-057 | F-D0047-059 | 2 |
| 臺北市 | F-D0047-061 | F-D0047-063 | 12 |
| 高雄市 | F-D0047-065 | F-D0047-067 | 38 |
| 新北市 | F-D0047-069 | F-D0047-071 | 29 |
| 臺中市 | F-D0047-073 | F-D0047-075 | 29 |
| 臺南市 | F-D0047-077 | F-D0047-079 | 37 |
| 連江縣 | F-D0047-081 | F-D0047-083 | 4 |
| 金門縣 | F-D0047-085 | F-D0047-087 | 6 |

合計 368 個鄉鎮市區。

> 全臺灣合併資料集 `F-D0047-089`／`091` 只提供 **22 個縣市層級**的預報點，並非 368 個鄉鎮，因此本模組改用逐縣市資料集。

---

## 資料結構

每個 JSON 檔內容為該縣市的 `records.Locations` 清單：

```json
[
    {
        "DatasetDescription": "臺灣各鄉鎮市區未來3天天氣預報",
        "LocationsName": "臺北市",
        "Dataid": "D0047",
        "Location": [
            {
                "LocationName": "中正區",
                "Geocode": "63000050",
                "Latitude": "25.032404",
                "Longitude": "121.518419",
                "WeatherElement": [
                    {
                        "ElementName": "溫度",
                        "Time": [
                            {
                                "DataTime": "2026-08-26T18:00:00+08:00",
                                "ElementValue": [{"Temperature": "30"}]
                            }
                        ]
                    }
                ]
            }
        ]
    }
]
```

---

## 更新時機

鄉鎮預報一天發布 4 次：每日 `05:30`、`11:30`、`17:30`、`23:30`，更新頻率為每 6 小時。實際天氣與預報差異較大時也可能即時更新。排程建議設在發布時間之後。

---

## 相關模組

CODIS 觀測資料擷取見 [天氣爬蟲](weather-crawler.md)；後續轉表格處理見 [JSON 轉 DataFrame](json-to-dataframe.md)；層級定位見 [架構概覽](architecture.md)。
