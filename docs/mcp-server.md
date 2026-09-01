# MCP Server

`pygreenbuild` 提供 **MCP Server**（Model Context Protocol），讓 AI Agent（Cursor、Claude Code、Codex 等）可直接呼叫套件函式，無需手寫 Python 腳本。

## 架構

```
src/pygreenbuild/mcp/
├─ server.py           # ★ 統一 MCP 窗口（FastMCP + stdio）
├─ serialization.py    # DataFrame ↔ JSON records、統一回傳 dict
└─ tools/              # 依領域註冊 @mcp.tool()，直接呼叫核心函式
```

統一入口為 [`src/pygreenbuild/mcp/server.py`](../src/pygreenbuild/mcp/server.py)，所有 tools 透過單一 `FastMCP("pygreenbuild")` 實例註冊。

## 安裝

```bash
pip install -e ".[mcp]"
```

> 相依 `mcp>=1.6.0,<2`（FastMCP API）。MCP SDK 2.x 已將 FastMCP 更名為 MCPServer，後續可另行遷移。

或從 GitHub 安裝：

```bash
pip install "pygreenbuild[mcp] @ git+https://github.com/Lucy-icdi/pygreenbuild.git"
```

## 環境變數

| 變數 | 用途 | 必填 |
|------|------|------|
| `CWA_API_KEY` | CWA OpenData 授權碼（鄉鎮預報 tools） | 使用 CWA 預報時必填 |
| `PYGREENBUILD_DB_URL` | SQLAlchemy 連線字串（`fill_sql_table_na`） | 使用 DB tool 時必填 |

> **安全限制**：DB 寫入（`apply_filled_na`）不對 MCP 開放；`fill_sql_table_na` 僅唯讀預覽。

## 客戶端整合

以下各節假設你已在本機安裝 `pygreenbuild[mcp]`，且 `pygreenbuild-mcp` 可在 PATH 中找到（或改用下方範例中的**完整路徑**）。

若使用專案虛擬環境，Windows 範例：

```text
D:\github\pygreenbuild\.venv\Scripts\pygreenbuild-mcp.exe
```

Linux / macOS 範例：

```text
/path/to/pygreenbuild/.venv/bin/pygreenbuild-mcp
```

### Cursor

在 Cursor 的 MCP 設定（Settings → MCP）中加入：

```json
{
  "mcpServers": {
    "pygreenbuild": {
      "command": "pygreenbuild-mcp",
      "env": {
        "CWA_API_KEY": "<your-cwa-api-key>"
      }
    }
  }
}
```

### Claude Code

Claude Code 支援 **CLI 新增** 或 **專案根目錄 `.mcp.json`**（可納入版本控制，團隊共用）。官方文件：[Claude Code MCP](https://docs.anthropic.com/en/docs/claude-code/mcp)。

#### 方式一：CLI（推薦）

在 `pygreenbuild` 專案目錄下執行：

```bash
# 僅本機、本專案（local scope，預設）
claude mcp add --env CWA_API_KEY=${CWA_API_KEY} pygreenbuild -- pygreenbuild-mcp

# 寫入專案 .mcp.json，可 commit 給團隊（project scope）
claude mcp add --scope project --env CWA_API_KEY=${CWA_API_KEY} pygreenbuild -- pygreenbuild-mcp
```

Windows 若 `pygreenbuild-mcp` 不在 PATH，改用 venv 完整路徑：

```powershell
claude mcp add --scope project --env CWA_API_KEY=$env:CWA_API_KEY pygreenbuild -- D:\github\pygreenbuild\.venv\Scripts\pygreenbuild-mcp.exe
```

驗證：

```bash
claude mcp list
claude mcp get pygreenbuild
```

首次使用 **project scope** 的 `.mcp.json` 時，需在互動式 `claude` 工作階段中**核准**該 MCP server。

#### 方式二：手動編輯 `.mcp.json`

在專案根目錄建立 `.mcp.json`：

```json
{
  "mcpServers": {
    "pygreenbuild": {
      "command": "pygreenbuild-mcp",
      "env": {
        "CWA_API_KEY": "${CWA_API_KEY}"
      }
    }
  }
}
```

- `${CWA_API_KEY}` 會從 shell 環境變數展開，**請勿**將 API key 硬編碼進版本庫。
- 需要 DB tool 時，可再加 `"PYGREENBUILD_DB_URL": "${PYGREENBUILD_DB_URL}"`。
- 亦可改用 JSON 一次匯入：`claude mcp add-json pygreenbuild '{"command":"pygreenbuild-mcp","env":{"CWA_API_KEY":"${CWA_API_KEY}"}}' --scope project`

#### 從 Claude Desktop 匯入

若已在 Claude Desktop 設定過 MCP，可一鍵匯入：

```bash
claude mcp add-from-claude-desktop
```

### Codex（OpenAI Codex CLI）

Codex 使用 **TOML** 設定檔，區段名稱必須是 **`mcp_servers`**（底線，不是 `mcpServers`）。官方文件：[Codex MCP](https://developers.openai.com/codex/mcp/)。

設定檔位置：

| 層級 | 路徑 | 說明 |
|------|------|------|
| 全域 | `~/.codex/config.toml` | 所有 Codex 工作階段 |
| 專案 | `.codex/config.toml` | 僅該專案；目錄需為 **trusted project** |

#### 方式一：CLI（推薦）

```bash
# 新增 stdio MCP server
codex mcp add pygreenbuild --env CWA_API_KEY=<your-cwa-api-key> -- pygreenbuild-mcp

# 列出與檢視
codex mcp list
codex mcp get pygreenbuild
```

Windows 範例（venv 完整路徑）：

```powershell
codex mcp add pygreenbuild --env CWA_API_KEY=$env:CWA_API_KEY -- D:\github\pygreenbuild\.venv\Scripts\pygreenbuild-mcp.exe
```

#### 方式二：手動編輯 `config.toml`

編輯 `~/.codex/config.toml`（或專案內 `.codex/config.toml`）：

```toml
[mcp_servers.pygreenbuild]
command = "pygreenbuild-mcp"
env = { CWA_API_KEY = "<your-cwa-api-key>" }
# 選用：DB 唯讀 tool
# env = { CWA_API_KEY = "<your-cwa-api-key>", PYGREENBUILD_DB_URL = "mysql+pymysql://..." }
```

使用 venv 時可指定完整 command：

```toml
[mcp_servers.pygreenbuild]
command = "D:/github/pygreenbuild/.venv/Scripts/pygreenbuild-mcp.exe"
env = { CWA_API_KEY = "<your-cwa-api-key>" }
```

#### 驗證連線

在 Codex 互動工作階段輸入：

```text
/mcp
```

應可看到 `pygreenbuild` 及其 tools 列表。

> **常見問題**：若設定被忽略，請確認 TOML 區段為 `[mcp_servers.xxx]`（不是 `[mcp-servers.xxx]`），且專案 scope 的 `.codex/config.toml` 所在目錄已被 Codex 標記為 trusted。

## 本機啟動

```bash
# 正式入口
pygreenbuild-mcp

# 或開發腳本
python scripts/run_mcp_server.py
```

## Tool 清單

### 天氣擷取（ingestion）

| Tool | 對應函式 | 說明 |
|------|---------|------|
| `codis_daily` | `codis_daily` | CODIS 日報 JSON |
| `codis_monthly` | `codis_monthly` | CODIS 月報 JSON |
| `codis_yearly` | `codis_yearly` | CODIS 年報 JSON |
| `codis_single_hourly_monthly` | `codis_single_hourly_monthly` | CODIS 單項逐時月報表 JSON |
| `codis_single_daily_yearly` | `codis_single_daily_yearly` | CODIS 單項逐日年報表 JSON |
| `codis_single_monthly_yearly` | `codis_single_monthly_yearly` | CODIS 單項逐月年報表 JSON |
| `cwa_township_forecast_3day` | `cwa_township_forecast_3day` | CWA 鄉鎮 3 天預報 |
| `cwa_township_forecast_week` | `cwa_township_forecast_week` | CWA 鄉鎮 1 週預報 |

### 資料轉換（transform）

| Tool | 對應函式 | 說明 |
|------|---------|------|
| `json_to_dataframe` | `json_to_dataframe` | CODIS JSON → 中文欄位表 |
| `to_date_column` | `to_date_column` | 欄位轉純日期 |
| `to_time_column` | `to_time_column` | 欄位轉純時間 |
| `to_datetime_column` | `to_datetime_column` | 欄位轉日期時間 |
| `fill_time_gaps` | `fill_time_gaps` | 補齊時間缺口 |
| `fill_dataframe_na` | `fill_dataframe_na` | 填補孤立 NA |
| `pmv_iso` | `pmv_iso` | ISO 7730 PMV/PPD |
| `pmv_ashrae` | `pmv_ashrae` | ASHRAE 55 PMV/PPD |

### 資料合併（load）

| Tool | 對應函式 | 說明 |
|------|---------|------|
| `codis_merge` | `codis_merge` | 合併 CODIS JSON |
| `codis_hour_merge` | `codis_hour_merge` | 合併小時資料 |
| `codis_day_merge` | `codis_day_merge` | 合併日資料 |
| `codis_month_merge` | `codis_month_merge` | 合併月資料 |

### 冰水主機 KPI（metrics）

| Tool | 說明 |
|------|------|
| `chiller_usrt_single` | 單台冰水主機 USRT/kW |
| `chiller_usrt_zone_pumps` | 多區域泵加總 |
| `chiller_usrt_ice_melt` | 融冰 USRT |
| `chiller_usrt_batch` | 批次 USRT |
| `chiller_cop` | COP |
| `chiller_eer` | EER |
| `chiller_power_rate` | 耗電率 |
| `chiller_kw_to_usrt` | kW → USRT |
| `chiller_performance_batch` | 批次 COP/EER/耗電率 |

### 資料庫（唯讀）

| Tool | 說明 |
|------|------|
| `fill_sql_table_na` | 讀表 + 填補 NA 預覽（不回寫） |

## 回傳格式

序列化由 [`src/pygreenbuild/mcp/serialization.py`](../src/pygreenbuild/mcp/serialization.py) 處理。所有 tools 回傳統一 dict：

```python
{"success": True, "message": "ok", "result": ...}
```

DataFrame 結果序列化為 JSON records：

```python
{
    "format": "records",
    "columns": ["觀測時間", "氣溫"],
    "data": [{"觀測時間": "2024-01-01T00:00:00", "氣溫": 25.0}],
    "row_count": 1
}
```

## Python 使用範例（不透過 MCP）

不經 MCP 時請直接呼叫核心函式，不必經過 tools：

```python
from pygreenbuild.transform import pmv_iso
from pygreenbuild import ChillerKPI

comfort = pmv_iso(
    tdb=25.0, tr=25.0, vr=0.1, rh=50.0, met=1.2, clo=0.5
)
print(comfort["pmv"])

cop = ChillerKPI.calculate_cop(cooling_kw=1000.0, power_kw=200.0)
print(cop)  # 5.0
```

## 例外

| 情況 | 行為 |
|------|------|
| 缺少 `CWA_API_KEY` | `success=False`，message 提示設定環境變數 |
| 缺少 `PYGREENBUILD_DB_URL` | `success=False`，message 提示設定環境變數 |
| CODIS 下載失敗 | `success=False`，message 含 API 錯誤原因 |
| 空 data list 傳入 transform tools | 拋出 `ValueError` |

## 使用限制

- 僅支援 **stdio** transport（本機 Agent 整合）
- DataFrame 輸入須為 JSON records（`list[dict]`）
- 大型結果（>5000 列）建議 Agent 分段處理
- DB 寫入操作不對 MCP 開放

## 相關文件

- [架構概覽](architecture.md)
- [專案資料夾規劃](folder-structure.md)
- 各函式詳細說明見對應 docs 篇章
