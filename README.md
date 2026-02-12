# pygreenbuild
Weather data crawler and WRF forecast correction for GreenBIM applications

## 開始使用

### 1. 建立虛擬環境（推薦）
```bash
# 建立虛擬環境
python -m venv .venv

# 啟動虛擬環境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

### 2. 安裝套件
```bash
# 從 GitHub 安裝
pip install git+https://github.com/Lucy-icdi/pygreenbuild.git

```
### 天氣爬蟲 程式
```python
from pygreenbuild.weather_crawler import codis_yearly, codis_monthly, codis_daily

#年報表
codis_yearly(station_id="466920",output_dir= "test_output", year=2025)

#月報表
codis_monthly(station_id="466920",output_dir= "test_output",setDate= "2024-11-01")

#日報表_多日
codis_daily("466920","test_output","2024-11-01","2024-11-30")

```

## 維護指令

### 更新套件
```bash
pip install --upgrade git+https://github.com/Lucy-icdi/pygreenbuild.git
```

### 卸載套件
```bash
pip uninstall pygreenbuild
```

### 退出虛擬環境
```bash
deactivate
```
