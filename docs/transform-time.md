# 時間欄位轉換（transform.transform_time）

模組：`pygreenbuild.transform.transform_time`  
匯入：

```python
from pygreenbuild.transform import (
    to_date_column,
    to_time_column,
    to_datetime_column,
)
```

將 DataFrame 指定欄位轉成純日期、純時間，或日期時間。

---

## `to_date_column`（純日期）

### 用途

將指定欄位轉換為 `datetime.date`。支援：

- `2025/08/15`、`2025/8/15`
- `2025-08-15`、`2025-8-15`
- `20250815`

若值為完整日期時間字串，只取日期部分。

### 輸入參數

| 參數 | 型別 | 單位 | 意義 |
|------|------|------|------|
| `df` | `pd.DataFrame` | 不適用 | 輸入資料表 |
| `column` | `str` | 不適用 | 要轉換的欄位名稱 |
| `result_col` | `str \| None` | 不適用 | 結果欄位名；`None`（預設）則覆寫 `column` |
| `errors` | `Literal["raise", "coerce"]` | 不適用 | 失敗時：`raise` 拋例外，`coerce` 寫入 `None` |
| `as_string` | `bool` | 不適用 | `True` 輸出 `YYYY-MM-DD` 字串；`False`（預設）維持 `datetime.date` |

### 回傳值

| 型別 | 單位 | 意義 |
|------|------|------|
| `pd.DataFrame` | 不適用 | 含日期欄的新資料表；不修改原表。元素為 `datetime.date`、字串（`as_string=True`）或 `None` |

### 使用範例

```python
import pandas as pd
from pygreenbuild.transform import to_date_column

df = pd.DataFrame(
    {
        "d": [
            "2025/08/15",
            "2025/8/15",
            "2025-08-15",
            "2025-8-15",
            "20250815",
        ]
    }
)
out = to_date_column(df, "d")
# out["d"].iloc[0] → datetime.date(2025, 8, 15)

out_str = to_date_column(df, "d", as_string=True)
# out_str["d"].iloc[0] → "2025-08-15"
```

### 可能例外

| 例外 | 條件 |
|------|------|
| `KeyError` | `column` 不在 `df.columns` |
| `ValueError` | `errors` 非法；或 `errors="raise"` 且有無法解析的值 |

### 使用限制與注意事項

- 空字串、`None`、`NaN` 轉成 `None`。
- 回傳 `df.copy()`，不原地修改。

---

## `to_time_column`（純時間）

### 用途

將指定欄位轉換為 `datetime.time`。支援：

- `14:00:15`、`14:00`
- `140015`

若值為完整日期時間字串，只取時間部分。

若小時為 `23` 且分鐘為 `59`（`23:59:00`–`23:59:59`），一律視為 `00:00:00`（代表隔天午夜，例如 `23:59:01` → `00:00:00`）。

### 輸入參數

| 參數 | 型別 | 單位 | 意義 |
|------|------|------|------|
| `df` | `pd.DataFrame` | 不適用 | 輸入資料表 |
| `column` | `str` | 不適用 | 要轉換的欄位名稱 |
| `result_col` | `str \| None` | 不適用 | 結果欄位名；`None`（預設）則覆寫 `column` |
| `errors` | `Literal["raise", "coerce"]` | 不適用 | 失敗時：`raise` 拋例外，`coerce` 寫入 `None` |
| `as_string` | `bool` | 不適用 | `True` 輸出 `HH:MM:SS` 字串；`False`（預設）維持 `datetime.time` |

### 回傳值

| 型別 | 單位 | 意義 |
|------|------|------|
| `pd.DataFrame` | 不適用 | 含時間欄的新資料表；不修改原表。元素為 `datetime.time`、字串（`as_string=True`）或 `None` |

### 使用範例

```python
import pandas as pd
from pygreenbuild.transform import to_time_column

df = pd.DataFrame({"t": ["14:00:15", "14:00", "140015", "23:59", "23:59:01"]})
out = to_time_column(df, "t")
# out["t"].iloc[0] → datetime.time(14, 0, 15)
# out["t"].iloc[3] → datetime.time(0, 0)     # 23:59 → 00:00:00
# out["t"].iloc[4] → datetime.time(0, 0)     # 23:59:01 → 00:00:00

out_str = to_time_column(df, "t", as_string=True)
# out_str["t"].iloc[0] → "14:00:15"
# out_str["t"].iloc[3] → "00:00:00"
```

### 可能例外

| 例外 | 條件 |
|------|------|
| `KeyError` | `column` 不在 `df.columns` |
| `ValueError` | `errors` 非法；或 `errors="raise"` 且有無法解析的值 |

### 使用限制與注意事項

- 空字串、`None`、`NaN` 轉成 `None`。
- 純日期物件無法轉成時間（`raise` 會失敗，`coerce` 為 `None`）。
- `23:59:00`–`23:59:59` 一律視為 `00:00:00`（代表隔天午夜）；例如 `23:59:01` → `00:00:00`。
- `as_string=True` 時空值仍為 `None`（非整空白字串）。

---

## `to_datetime_column`（日期時間）

### 用途

將指定欄位轉換為 pandas 日期時間（`datetime64`）。支援：

- `2025/08/15 14:00:15`、`2025/8/15 14:00:15`
- `2025-08-15 14:00:15`、`2025-8-15 14:00:15`
- `2025/08/15T14:00:15`、`2025-08-15T14:00:15`（ISO「T」分隔）
- `2025-08-15T14:00`、`2025/08/15 14:00`（僅到分）
- `20250815140015`

若值僅有日期（無時間），時間補為 `00:00:00`。

若小時為 `23` 且分鐘為 `59`（`23:59:00`–`23:59:59`），一律視為隔天 `00:00:00`
（例如 `2025-08-15 23:59:01` → `2025-08-16 00:00:00`）。

### 輸入參數

| 參數 | 型別 | 單位 | 意義 |
|------|------|------|------|
| `df` | `pd.DataFrame` | 不適用 | 輸入資料表 |
| `column` | `str` | 不適用 | 要轉換的欄位名稱 |
| `result_col` | `str \| None` | 不適用 | 結果欄位名；`None`（預設）則覆寫 `column` |
| `errors` | `Literal["raise", "coerce"]` | 不適用 | 失敗時：`raise` 拋例外，`coerce` 寫入 `NaT` |
| `as_string` | `bool` | 不適用 | `True` 輸出 `YYYY-MM-DD HH:MM:SS` 字串；`False`（預設）維持 `datetime64`／`Timestamp` |

### 回傳值

| 型別 | 單位 | 意義 |
|------|------|------|
| `pd.DataFrame` | Timestamp（納秒）或字串 | 含日期時間欄的新資料表；不修改原表。`as_string=True` 時空值為 `None` |

### 使用範例

```python
import pandas as pd
from pygreenbuild.transform import to_datetime_column

df = pd.DataFrame(
    {
        "ts": [
            "2025/08/15 14:00:15",
            "2025/8/15 14:00:15",
            "2025-08-15 14:00:15",
            "2025-8-15 14:00:15",
            "2025/08/15T14:00:15",
            "2025-08-15T14:00:15",
            "2025-08-15T14:00",
            "20250815140015",
            "2025-08-15 23:59",
            "2025-08-15 23:59:01",
        ]
    }
)
out = to_datetime_column(df, "ts")
print(out["ts"].dtype)  # datetime64[ns]
# out["ts"].iloc[8] → 2025-08-16 00:00:00
# out["ts"].iloc[9] → 2025-08-16 00:00:00

out_str = to_datetime_column(df, "ts", as_string=True)
# out_str["ts"].iloc[0] → "2025-08-15 14:00:15"
# out_str["ts"].iloc[8] → "2025-08-16 00:00:00"
```

### 可能例外

| 例外 | 條件 |
|------|------|
| `KeyError` | `column` 不在 `df.columns` |
| `ValueError` | `errors` 非法；或 `errors="raise"` 且有無法解析的值 |

### 使用限制與注意事項

- 空字串、`None`、`NaN`：`as_string=False` 轉成 `NaT`；`as_string=True` 轉成 `None`。
- 同一欄可混用上述支援格式（含空白分隔與 ISO「T」分隔）。
- 僅到分的字串（如 `2025-08-15T14:00`）秒數補為 `00`。
- 緊湊日期時間須為完整 14 碼（`YYYYMMDDHHMMSS`）。
- `23:59:00`–`23:59:59` 一律視為隔天 `00:00:00`（代表隔天午夜）。
