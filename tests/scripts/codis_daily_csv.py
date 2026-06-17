import json
import os
import sys

import pandas as pd  # 引入 pandas 用於時間修正

# 將專案 src 目錄加入模組搜尋路徑，確保從 workspace 根目錄執行時可匯入 pygreenbuild
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from pygreenbuild.ingestion.weather_crawler.codis_crawler_tojson import codis_daily
from pygreenbuild.transform.detector import detect_mapping
from pygreenbuild.transform.json_to_dataframe import json_to_dataframe


def main():
    station_id = "C2C480"

    # 修正輸出位置：使用絕對路徑，確保不論在哪裡執行，都會定位在 tests/data
    output_dir = os.path.join(ROOT_DIR, "tests", "data")

    start_date = "2026-05-01"
    end_date = "2026-05-31"

    print("=== 開始下載 codis_daily JSON ===")
    success, message = codis_daily(station_id, output_dir, start_date, end_date)
    print(message)

    if not success:
        print("下載失敗，無法轉換。")
        return

    json_filename = f"{start_date}~{end_date}_{station_id}.json"
    json_path = os.path.join(output_dir, json_filename)

    if not os.path.isfile(json_path):
        print(f"找不到下載後的 JSON 檔案：{json_path}")
        return

    print(f"=== 讀取 JSON：{json_path} ===")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        column_mapping = detect_mapping(data)
    except ValueError as exc:
        print(f"無法偵測 JSON 格式：{exc}")
        return

    print("=== 轉換 JSON 為 DataFrame (保留原中文化欄位對應) ===")
    df = json_to_dataframe(data, column_mapping)

    # ==================== 時間修正核心程式碼 ====================
    # 根據實測輸出的 Excel，中文化後的欄位名稱為 '觀測時間'
    time_col = "觀測時間"

    if time_col in df.columns:
        print(
            f"=== 偵測到時間欄位 '{time_col}'，將 23:59:00 加上 1 分鐘進位至隔天 00:00:00 ==="
        )
        # 1. 先轉為 Pandas datetime 物件以進行時間運算
        df[time_col] = pd.to_datetime(df[time_col])

        # 2. 找出所有時間剛好為 23 點 59 分的資料列
        mask = (df[time_col].dt.hour == 23) & (df[time_col].dt.minute == 59)

        # 3. 加上 1 分鐘（會自動跨日並把分鐘、秒數歸零）
        df.loc[mask, time_col] = df.loc[mask, time_col] + pd.Timedelta(minutes=1)

        # 4. 轉回與氣象署一致的 ISO 字串格式 (例如：2026-04-02T00:00:00)
        df[time_col] = df[time_col].dt.strftime("%Y-%m-%dT%H:%M:%S")
    else:
        print(
            f"警告：找不到時間欄位 '{time_col}'，目前 DataFrame 欄位有: {list(df.columns)}"
        )
    # ==========================================================

    # 確保輸出目錄存在
    os.makedirs(output_dir, exist_ok=True)

    csv_filename = f"{start_date}~{end_date}_{station_id}.csv"
    csv_path = os.path.join(output_dir, csv_filename)

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"=== 轉換完成，CSV 已輸出：{csv_path} ===")


if __name__ == "__main__":
    main()
