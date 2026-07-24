# 天氣爬蟲

從頂層套件可直接匯入 CODIS 年／月／日報擷取函式：

```python
from pygreenbuild import codis_yearly, codis_monthly, codis_daily
```

實作位於 `pygreenbuild.ingestion.weather_crawler`。

## 年報

```python
codis_yearly(station_id="466920", output_dir="test_output", year=2025)
```

| 參數 | 說明 |
|------|------|
| `station_id` | CWA 測站代號（例：臺北 `466920`） |
| `output_dir` | 輸出目錄 |
| `year` | 年份 |

## 月報

```python
codis_monthly(station_id="466920", output_dir="test_output", setDate="2024-11-01")
```

| 參數 | 說明 |
|------|------|
| `setDate` | 該月任一日（`YYYY-MM-DD`），用來指定月份 |

## 日報（區間）

```python
codis_daily("466920", "test_output", "2024-11-01", "2024-11-30")
```

依起始與結束日期擷取日報資料並寫入 `output_dir`。

## 相關模組

同目錄尚有 Cookie 管理、CWA 測站清單、GreenBIM／ICDI API 下載與匯出等工具；天氣來源取得後，可再經 `parsers`／`transform` 進入標準化管線。詳見 [架構概覽](architecture.md)。
