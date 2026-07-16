import os
import sys

# 將專案 src 目錄加入模組搜尋路徑，確保從 workspace 根目錄執行時可匯入 pygreenbuild
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from pygreenbuild.ingestion.weather_crawler.codis_crawler_tojson import codis_daily
from pygreenbuild.transform import json_to_dataframe


def main():
    station_id = "C2C480"

    # 修正輸出位置：使用絕對路徑，確保不論在哪裡執行，都會定位在 tests/data
    output_dir = os.path.join(ROOT_DIR, "tests", "data")

    start_date = "2026-06-01"
    end_date = "2026-06-25"

    print("=== 開始下載 codis_daily 資料 ===")
    success, data, message = codis_daily(
        station_id, None, start_date, end_date, return_data=True
    )
    print(message)

    if not success or data is None:
        print("下載失敗，無法轉換。")
        return

    print("=== 轉換資料為 DataFrame (保留原中文化欄位對應) ===")
    try:
        df = json_to_dataframe(data)
    except ValueError as exc:
        print(f"無法轉換 JSON：{exc}")
        return

    # 確保輸出目錄存在
    os.makedirs(output_dir, exist_ok=True)

    csv_filename = f"{start_date}~{end_date}_{station_id}.csv"
    csv_path = os.path.join(output_dir, csv_filename)

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"=== 轉換完成，CSV 已輸出：{csv_path} ===")


if __name__ == "__main__":
    main()
