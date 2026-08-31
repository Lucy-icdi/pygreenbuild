# 孤立 NA 填補（資料庫／DataFrame／寫回）

模組：

- `pygreenbuild.ingestion.ems_db.factory_db` → `fill_sql_table_na`（只從資料庫讀取）
- `pygreenbuild.transform.fill_dataframe_na` → `fill_dataframe_na`（回傳新的完整 DataFrame）
- `pygreenbuild.load.apply_filled_na` → 將 `fill_sql_table_na` 結果寫回 DB 或匯出 SQL

（內建上下夾住 NA 演算法為套件內部實作，不對外匯出。）

匯入：

```python
from pygreenbuild.ingestion.ems_db import fill_sql_table_na
from pygreenbuild.transform import fill_dataframe_na
from pygreenbuild.load import apply_filled_na
```

兩個填補入口：

- `fill_sql_table_na`：從資料庫讀取 → 回傳 `dict`（可接 `apply_filled_na`）
- `fill_dataframe_na`：回傳**新的**已填補完整 DataFrame（不改原表、不轉 dict）

兩者皆以 `fill_method` 填補「上下皆有值、本身為 NA」的孤立缺口。

---

## `fill_sql_table_na`

### 用途

**只從資料庫**讀取指定表，填補孤立 NA，回傳結構化 `dict`。  
記憶體中的 DataFrame 請改用 [`fill_dataframe_na`](#fill_dataframe_na)。

- 不傳範圍三參數：讀整張表。
- 三者同時指定：`BETWEEN` 篩選並升冪排序。
- `exclude_cols`／`key_cols`／`fill_method`：見下表。

### 輸入參數

| 參數 | 型別 | 單位 | 意義 |
|------|------|------|------|
| `connection_str` | `str` | 不適用 | SQLAlchemy 連線字串 |
| `table_name` | `str` | 不適用 | 資料表名稱 |
| `range_col` | `str \| None` | 不適用 | 可選範圍欄 |
| `range_start` / `range_end` | 依欄位而定 \| `None` | 依欄位而定 | 可選起迄（須與 `range_col` 同時給） |
| `exclude_cols` | `list[str] \| None` | 不適用 | 不填補的欄 |
| `key_cols` | `list[str] \| None` | 不適用 | 回傳定位欄；有給則精簡 `records` |
| `fill_method` | `Literal[...]` | 不適用 | 填值策略 |
| `fill_value` | `object \| None` | 依欄位而定 | `constant` 時必填 |
| `columns` | `list[str] \| None` | 不適用 | 只填這些欄；省略則除排除欄外全部填 |
| `engine` | `Engine \| None` | 不適用 | 可選既有 engine |

#### `fill_method`

| 值 | 意義 |
|----|------|
| `"neighbor_mean"` | 上下平均（對齊小數位數） |
| `"ffill"` / `"bfill"` | 向下／向上填補 |
| `"constant"` | 指定常數 |

僅處理「上下皆有值、本身為 NA」的孤立缺口。

### 回傳值

`table_name`、`records`、`filled_cols`、`n_filled_cells`、`fill_method` 等（單位：不適用）。

### 使用範例

```python
from pygreenbuild.ingestion.ems_db import fill_sql_table_na

db_connection_str = "mysql+pymysql://user:password@host:3306/dbname"

result = fill_sql_table_na(
    db_connection_str,
    table_name="c2c480",
    range_col="DateTime",
    range_start=2026040100,
    range_end=2026073123,
    exclude_cols=["最大瞬間風時間"],
    key_cols=["DateTime"],
    fill_method="neighbor_mean",
)
```

### 可能例外／注意事項

- 會組進 SQL 的識別字（`table_name`、`range_col`，以及 `apply_filled_na` 的表名／`key_cols`／更新欄）可含中文，但禁止引號、分號、控制字元。
- `exclude_cols`、`key_cols`、`columns` 只用於填補／精簡結果，不組進 SELECT，故不做識別字檢查。
- 範圍三參數須全給或全省略。
- **不寫回**資料庫；請接 [`apply_filled_na`](#apply_filled_na)。

---

## `fill_dataframe_na`

### 用途

填補 pandas DataFrame 的孤立 NA，回傳**一份新的完整 DataFrame**（不修改原表、不轉 dict）。  
若要寫回資料庫，請用 `fill_sql_table_na` + `apply_filled_na`。

### 輸入參數

| 參數 | 型別 | 單位 | 意義 |
|------|------|------|------|
| `df` | `pd.DataFrame` | 不適用 | 輸入表（不會被修改） |
| `range_col` / `range_start` / `range_end` | 同左 | 依欄位而定 | 可選；只填此範圍內的列 |
| `exclude_cols` | `list[str] \| None` | 不適用 | 不填補的欄；`range_col` 會自動排除 |
| `fill_method` / `fill_value` | 同左 | 不適用 | 填值策略 |
| `columns` | `list[str] \| None` | 不適用 | 只填這些欄 |

欄名不經 SQL 識別字檢查（此函數不組 SQL）。中文欄名可直接使用。

### 回傳值

| 型別 | 單位 | 意義 |
|------|------|------|
| `pd.DataFrame` | 不適用 | 已填補的新表（完整列／欄，與輸入同形狀） |

### 使用範例

```python
import pandas as pd
from pygreenbuild.transform import fill_dataframe_na

df = pd.DataFrame(
    {
        "DateTime": [2026040100, 2026040101, 2026040102],
        "temp": [20.0, None, 24.0],
    }
)

filled = fill_dataframe_na(df, exclude_cols=["DateTime"], fill_method="neighbor_mean")
# filled 是新表；df 維持原樣；filled.loc[1, "temp"] == 22.0
```

### 可能例外

| 例外 | 條件 |
|------|------|
| `TypeError` | `df` 不是 DataFrame |
| `ValueError` | 範圍參數不完整；沒有可填補欄位 |
| `KeyError` | 指定欄位不存在 |

---

## `apply_filled_na`

### 用途

承接 `fill_sql_table_na` 的 `result`（dict），依 `key_cols` 對資料庫執行 `UPDATE`；或以 `sql_only=True` 只輸出 SQL 指令檔並打印前 5 筆。

### 輸入參數

| 參數 | 型別 | 單位 | 意義 |
|------|------|------|------|
| `result` | `dict` | 不適用 | 須含 `table_name`、`key_cols`、`records` |
| `connection_str` | `str \| None` | 不適用 | `sql_only=False` 且未傳 `engine` 時必填 |
| `sql_only` | `bool` | 不適用 | `True`＝只寫 SQL 檔並打印前 5 筆；`False`＝直接執行 |
| `sql_path` | `str \| Path \| None` | 不適用 | SQL 檔路徑 |
| `engine` | `Engine \| None` | 不適用 | 可選既有 engine |

### 使用範例

```python
from pygreenbuild.ingestion.ems_db import fill_sql_table_na
from pygreenbuild.load import apply_filled_na

result = fill_sql_table_na(
    db_connection_str,
    table_name="c2c480",
    range_col="DateTime",
    range_start=2026070100,
    range_end=2026073123,
    exclude_cols=["最大瞬間風時間"],
    key_cols=["DateTime"],
    fill_method="neighbor_mean",
)

apply_filled_na(result, sql_only=True, sql_path="c2c480_filled_na.sql")
apply_filled_na(result, db_connection_str, sql_only=False)
```

### 注意事項

- 必須指定 `key_cols`，寫回才有 `WHERE`。
- 建議先 `sql_only=True` 檢查，再改 `False` 寫入。
