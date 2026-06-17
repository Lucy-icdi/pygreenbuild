import pandas as pd
import requests
import datetime
import os
import time
from psychrolib import SetUnitSystem, GetTWetBulbFromRelHum, SI


def export_wrf3km(lat, lon, account, password, output_path="wrf3km.csv", to_csv=False):
    url = f"https://www.weatherservice.org.tw/ForecastData_getData?account={account}&pwd={password}&x={lon}&y={lat}"

    try:
        # 1. 獲取並解析資料
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        df = pd.json_normalize(response.json(), record_path='data')

        if df.empty:
            print("⚠️ 無資料可供處理。")
            return None
        # 2. 計算濕球溫度
        SetUnitSystem(SI)
        df['wet'] = df.apply(
            lambda row: GetTWetBulbFromRelHum(
                row['T'],
                row['RH'] / 100,
                row['P'] * 100
            ), axis=1
        ).round(2)
        # 3. 根據 to_csv 參數決定輸出方式
        if to_csv:
            # 確保目錄存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 如果路徑只有檔名，沒有副檔名，自動加上日期和 .csv
            if not output_path.lower().endswith('.csv'):
                today_str = datetime.date.today().strftime('%Y%m%d')
                base_name = os.path.splitext(output_path)[0]
                output_path = f"{base_name}_{today_str}.csv"

            # 4. 匯出 CSV (使用 utf-8-sig 確保 Excel 開啟不亂碼)
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"✅ CSV 檔案已成功產出：{output_path}")
            return output_path
        else:
            # 不匯出 CSV，直接返回 DataFrame
            print("✅ 資料處理完成，返回 DataFrame")
            return df

    except Exception as e:
        print(f"❌ 處理失敗，錯誤原因: {e}")
        return None
