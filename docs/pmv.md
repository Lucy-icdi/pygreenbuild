# PMV / PPD 舒適度計算（transform.pmv）

模組：`pygreenbuild.transform.pmv`  
匯入：

```python
from pygreenbuild.transform import pmv_iso, pmv_ashrae
```

依 ISO 7730 與 ASHRAE 55 計算預測平均投票（PMV, Predicted Mean Vote）與預測不滿意百分比（PPD, Predicted Percentage of Dissatisfied）。僅依賴 Python 標準庫。

演算對齊 [pythermalcomfort](https://github.com/pythermalcomfort/pythermalcomfort) 的 Fanger PMV、Gagge two-node SET 與 Cooling Effect 路徑。

---

## `pmv_iso`

### 用途

計算 **ISO 7730:2025** 的 PMV／PPD（Fanger 公式，Annex D 數值演算法）。

### 輸入參數

| 參數 | 型別 | 單位 | 意義 |
| --- | --- | --- | --- |
| `tdb` | `float \| Sequence[float]` | °C | 空氣乾球溫度 |
| `tr` | `float \| Sequence[float]` | °C | 平均輻射溫度 |
| `vr` | `float \| Sequence[float]` | m/s | 相對風速（含活動引起之相對風速，非單純感測風速） |
| `rh` | `float \| Sequence[float]` | % | 相對濕度 |
| `met` | `float \| Sequence[float]` | met | 代謝率 |
| `clo` | `float \| Sequence[float]` | clo | 衣著基本隔熱值（intrinsic clothing insulation） |
| `wme` | `float \| Sequence[float]` | met | 外部做功；預設 `0.0` |
| `round_output` | `bool` | 不適用 | 關鍵字參數；`True` 時 PMV 取小數 2 位、PPD 取小數 1 位 |
| `output` | `Literal[...]` | 不適用 | 關鍵字參數；決定回傳內容，見下表；預設 `"all"` |

每個環境參數可為單一數值，或長度相同的 list／tuple（長度為 1 的序列會廣播）。

#### `output` 選項（ISO）

| 值 | 回傳內容 |
| --- | --- |
| `"all"` | 完整結果字典（預設） |
| `"pmv"` | 只回傳 PMV |
| `"ppd"` | 只回傳 PPD |
| `"tsv"` | 只回傳熱感分類 |
| `"standard"` | 只回傳標準名稱 |

### 回傳值

| `output` | 純量輸入 | 向量化輸入 |
| --- | --- | --- |
| `"all"` | `dict[str, Any]` | `list[dict[str, Any]]` |
| 其他單一欄位 | 該欄位值（`float`／`str`） | 該欄位值的 `list` |

`output="all"` 時字典欄位：

| 鍵 | 型別 | 單位 | 意義 |
| --- | --- | --- | --- |
| `pmv` | `float` | 不適用（約 -3～+3） | 預測平均投票 |
| `ppd` | `float` | % | 預測不滿意百分比 |
| `tsv` | `str` | 不適用 | 熱感分類（Cold／Cool／Slightly Cool／Neutral／Slightly Warm／Warm／Hot） |
| `standard` | `str` | 不適用 | 固定為 `"ISO 7730:2025"` |

### 使用範例

```python
from pygreenbuild.transform import pmv_iso

result = pmv_iso(25.0, 25.0, 0.1, 50.0, 1.2, 0.5)
print(result)
# {'pmv': 0.08, 'ppd': 5.1, 'tsv': 'Neutral', 'standard': 'ISO 7730:2025'}

# 只取 PMV，方便寫入 DataFrame
pmv_only = pmv_iso(25.0, 25.0, 0.1, 50.0, 1.2, 0.5, output="pmv")
print(pmv_only)  # 0.08

batch = pmv_iso(
    tdb=[22.0, 25.0],
    tr=[22.0, 25.0],
    vr=0.1,
    rh=50.0,
    met=1.2,
    clo=0.5,
    output="pmv",
)
print(batch)  # [約 -0.72, 0.08]
```

寫入 pandas DataFrame：

```python
import pandas as pd
from pygreenbuild.transform import pmv_iso

df = pd.DataFrame(
    {
        "tdb": [22.0, 25.0, 28.0],
        "tr": [22.0, 25.0, 28.0],
        "vr": [0.1, 0.1, 0.1],
        "rh": [50.0, 50.0, 50.0],
    }
)

df["pmv"] = pmv_iso(
    df["tdb"].tolist(),
    df["tr"].tolist(),
    df["vr"].tolist(),
    df["rh"].tolist(),
    met=1.2,
    clo=0.5,
    output="pmv",
)
df["ppd"] = pmv_iso(
    df["tdb"].tolist(),
    df["tr"].tolist(),
    df["vr"].tolist(),
    df["rh"].tolist(),
    met=1.2,
    clo=0.5,
    output="ppd",
)
```

### 可能例外

| 例外 | 條件 |
| --- | --- |
| `ValueError` | 輸入非有限數；`vr < 0`；`rh` 不在 0～100；`met <= 0`；`clo < 0`；`wme` 不滿足 `0 <= wme < met`；序列長度不一致；`output` 不合法 |
| `RuntimeError` | 衣著表面溫度迭代未收斂 |

### 使用限制與注意事項

- `vr` 應為**相對風速**（感測風速 + 活動引起風速），不是單純風速計讀值。
- 本函式不做標準適用範圍裁切（不會因超出 ISO 建議範圍而回傳空值）；超出適用範圍時數值仍可算出，但解讀需自行判斷。
- ISO 7730 常見適用參考：約 `10 < tdb < 30` °C、`10 < tr < 40` °C、`0 < vr < 1` m/s、`0.8 < met < 4`、`0 < clo < 2`。
- 寫入 DataFrame 時，請將 Series 轉成 list（例如 `df["tdb"].tolist()`），目前不直接接受 pandas Series。

---

## `pmv_ashrae`

### 用途

計算 **ASHRAE 55-2023** 的 PMV／PPD。當相對風速 `vr > 0.1` m/s 時，先以 Gagge two-node SET 估算 Cooling Effect（CE），再以 `tdb - CE`、`tr - CE`、靜風 `0.1` m/s 代入 Fanger PMV。

### 輸入參數

參數名稱、型別、單位與意義同 [`pmv_iso`](#pmv_iso)。`output` 額外支援 ASHRAE 專屬欄位。

#### `output` 選項（ASHRAE）

| 值 | 回傳內容 |
| --- | --- |
| `"all"` | 完整結果字典（預設） |
| `"pmv"` | 只回傳 PMV |
| `"ppd"` | 只回傳 PPD |
| `"tsv"` | 只回傳熱感分類 |
| `"standard"` | 只回傳標準名稱 |
| `"cooling_effect"` | 只回傳 Cooling Effect |
| `"compliance"` | 只回傳是否落在 ±0.5 |

### 回傳值

回傳型別規則同 `pmv_iso`。`output="all"` 時除 ISO 欄位外，另含：

| 鍵 | 型別 | 單位 | 意義 |
| --- | --- | --- | --- |
| `standard` | `str` | 不適用 | 固定為 `"ASHRAE 55-2023"` |
| `cooling_effect` | `float` | °C | 高風速冷卻效應；`vr <= 0.1` 時為 `0` |
| `compliance` | `bool` | 不適用 | 是否滿足 `-0.5 < PMV < 0.5` |

### 使用範例

```python
from pygreenbuild.transform import pmv_ashrae

result = pmv_ashrae(25.0, 25.0, 0.5, 50.0, 1.2, 0.5)
print(result)
# {
#   'pmv': -0.69,
#   'ppd': 15.1,
#   'tsv': 'Slightly Cool',
#   'standard': 'ASHRAE 55-2023',
#   'cooling_effect': 2.62,
#   'compliance': False,
# }

print(pmv_ashrae(25.0, 25.0, 0.5, 50.0, 1.2, 0.5, output="cooling_effect"))
# 2.62

still = pmv_ashrae(25.0, 25.0, 0.1, 50.0, 1.2, 0.5, output="cooling_effect")
print(still)  # 0.0
```

### 可能例外

| 例外 | 條件 |
| --- | --- |
| `ValueError` | 同 `pmv_iso` |
| `RuntimeError` | PMV 衣著表面溫度或 SET 迭代未收斂 |

### 使用限制與注意事項

- Cooling Effect 僅在 `vr > 0.1` m/s 時計算；否則 CE 為 0，並直接以原風速計算 PMV。
- 本函式不做 ASHRAE 適用範圍裁切，也不實作「無風速控制權」時的風速上限規則。
- ASHRAE 55 常見適用參考：約 `10 < tdb < 40` °C、`10 < tr < 40` °C、`0 < vr < 2` m/s、`1 < met < 4`、`0 < clo < 1.5`。
- `compliance` 僅依 PMV 是否落在 ±0.5 判斷，不涵蓋標準中其他合規條件。

---

## 參考

- [pythermalcomfort](https://github.com/pythermalcomfort/pythermalcomfort)
- ISO 7730:2025（Fanger PMV／PPD）
- ASHRAE Standard 55-2023（含 elevated air speed／Cooling Effect）
