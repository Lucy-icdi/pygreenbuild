# 時間缺口補齊（transform.fill_time_gaps）

模組：`pygreenbuild.transform.fill_time_gaps`  
匯入：

```python
from pygreenbuild.transform import fill_time_gaps
```

依**手動指定**的時間頻率，補齊 DataFrame 中連續日期時間軸上缺失的列，並可選擇填值策略。

---

## `fill_time_gaps`

### 用途

當資料本來應為固定間隔（例如每小時、每 3 分鐘、每 5 分鐘一筆），但中間某些時間點整列消失時，自動插入缺失時間的列。其餘欄位預設為 `NA`，也可改為前一筆、後一筆、前後平均、指定值或中位數。

邊界取自 `datetime_col` 的最小值與最大值；頻率須由呼叫端以 `freq` 指定（不做自動偵測）。

### 輸入參數


| 參數             | 型別              | 單位    | 意義                                                               |
| -------------- | --------------- | ----- | ---------------------------------------------------------------- |
| `df`           | `pd.DataFrame`  | 不適用   | 輸入資料表                                                            |
| `datetime_col` | `str`           | 不適用   | 日期時間欄位名稱                                                         |
| `freq`         | `str`           | 不適用   | 時間頻率，如 `"h"、"4h"`、`"3min"`、`"5min"、"10min"`（pandas offset alias） |
| `fill_method`  | `Literal[...]`  | 不適用   | 填值策略，見下表；預設 `"na"`                                               |
| `fill_value`   | `object | None` | 依欄位而定 | 僅 `fill_method="constant"` 時必填的指定值                               |




#### `fill_method` 選項


| 值                 | 意義                                       |
| ----------------- | ---------------------------------------- |
| `"na"`            | 缺失維持 `NA`（預設）                            |
| `"ffill"`         | 以前一筆代替                                   |
| `"bfill"`         | 以後一筆代替                                   |
| `"neighbor_mean"` | 前後筆平均值（僅數值欄；缺前或後任一筆則維持 `NA`；非數值欄維持 `NA`） |
| `"constant"`      | 以 `fill_value` 代替                        |
| `"median"`        | 以該欄**原始資料**的中位數代替（僅數值欄；非數值欄維持 `NA`）      |




### 回傳值


| 型別             | 單位  | 意義                        |
| -------------- | --- | ------------------------- |
| `pd.DataFrame` | 不適用 | 補齊時間軸後的新表，依日期時間升冪排序；不修改原表 |




### 使用範例

```python
import pandas as pd
from pygreenbuild.transform import fill_time_gaps

df = pd.DataFrame(
    {
        "ts": pd.to_datetime(
            [
                "2025-08-15 10:00:00",
                "2025-08-15 12:00:00",
                "2025-08-15 13:00:00",
            ]
        ),
        "value": [10.0, 12.0, 13.0],
    }
)

# 預設：補上 11:00，value 為 NA
out_na = fill_time_gaps(df, "ts", "h")

# 前一筆代替 → 11:00 的 value = 10.0
out_ffill = fill_time_gaps(df, "ts", "h", fill_method="ffill")

# 前後平均 → 11:00 的 value = 11.0
out_mean = fill_time_gaps(df, "ts", "h", fill_method="neighbor_mean")

# 指定常數
out_const = fill_time_gaps(
    df, "ts", "h", fill_method="constant", fill_value=0.0
)

# 每 5 分鐘一筆
df5 = pd.DataFrame(
    {
        "ts": pd.to_datetime(
            ["2025-08-15 10:00:00", "2025-08-15 10:10:00"]
        ),
        "value": [1.0, 2.0],
    }
)
out5 = fill_time_gaps(df5, "ts", "5min")
# 會插入 10:05:00
```



### 可能例外


| 例外           | 條件                                                                                     |
| ------------ | -------------------------------------------------------------------------------------- |
| `TypeError`  | `df` 不是 `pandas.DataFrame`                                                             |
| `KeyError`   | `datetime_col` 不在 `df.columns`                                                         |
| `ValueError` | `freq` 為空或無法解析；`fill_method` 非法；`constant` 未給 `fill_value`；`df` 為空；日期時間含空值／無法解析；有重複時間戳 |




### 使用限制與注意事項

- 頻率必須手動指定，不會從資料自動推估。
- 日期時間欄不可有重複時間戳或空值（`NaT`／無法解析）。
- 回傳 `df` 的複本結果，不原地修改。
- 若原始資料含有不落在 `freq` 網格上的時間點，仍會保留，並與完整時間軸取聯集。
- `"neighbor_mean"` 與 `"median"` 只對數值欄生效；字串等非數值欄在這兩種策略下維持 `NA`。
- `"ffill"`／`"bfill"`／`"constant"` 會套用到所有非日期時間欄（含字串欄）。

