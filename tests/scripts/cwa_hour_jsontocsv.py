import pandas as pd
import json
import os

# === 設定區 ===
base_path = r"F:/BackUp/CODis/cwa_daily_data/現有站"  # 母資料夾路徑
output_base = r"F:/BackUp/CODis/cwa_daily_data/合併結果" # 輸出的總目錄
#years = ['2022', '2023', '2024', '2025']  # 定義要處理的年份清單
years = ['2020', '2021']  # 定義要處理的年份清單

# 定義目標欄位順序
target_columns = [
    '觀測時間', '測站氣壓', '海平面氣壓', '氣溫', '濕球溫度', 
    '露點溫度', '相對溼度', '風速', '風向', '十分鐘平均風速', 
    '十分鐘平均風向', '最大瞬間風風速', '最大瞬間風風向', '降水量', 
    '降水時數', '日照時數', '全天空日射量', '能見度', '總雲量', 
    '雲冪高', '紫外線指數'
]

# 獲取「現有站」下所有的測站 ID (子資料夾名稱)
all_stations = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]

# === 第一層：以年份為主迴圈 ===
for year in years:
    print(f"========== 正在處理 {year} 年度任務 ==========")
    
    # 建立該年份的專屬資料夾 (例如：合併結果/2025/)
    year_output_dir = os.path.join(output_base, str(year))
    os.makedirs(year_output_dir, exist_ok=True)
    
    # === 第二層：遍歷各個測站 ===
    for station_id in all_stations:
        station_folder = os.path.join(base_path, station_id)
        all_data = []
        
        # 篩選該測站內屬於該年份的檔案
        try:
            json_files = [f for f in os.listdir(station_folder) 
                         if f.startswith(str(year)) and f.endswith('.json')]
        except Exception:
            continue

        if not json_files:
            continue 

        # 讀取 JSON 並解析
        for file_name in json_files:
            file_path = os.path.join(station_folder, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry in data:
                        row = {
                            '觀測時間': entry.get('DataTime', '').replace('T', ' '),
                            '測站氣壓': entry.get('StationPressure', {}).get('Instantaneous'),
                            '海平面氣壓': entry.get('SeaLevelPressure', {}).get('Instantaneous'),
                            '氣溫': entry.get('AirTemperature', {}).get('Instantaneous'),
                            '濕球溫度': None, 
                            '露點溫度': entry.get('DewPointTemperature', {}).get('Instantaneous'),
                            '相對溼度': entry.get('RelativeHumidity', {}).get('Instantaneous'),
                            '風速': entry.get('WindSpeed', {}).get('Mean'),
                            '風向': entry.get('WindDirection', {}).get('Mean'),
                            '十分鐘平均風速': entry.get('WindSpeed', {}).get('TenMinutelyMaximum'),
                            '十分鐘平均風向': entry.get('WindDirection', {}).get('TenMinutelyMaximum'),
                            '最大瞬間風風速': entry.get('PeakGust', {}).get('Maximum'),
                            '最大瞬間風風向': entry.get('PeakGust', {}).get('Direction'),
                            '降水量': entry.get('Precipitation', {}).get('Accumulation'),
                            '降水時數': entry.get('PrecipitationDuration', {}).get('Total'),
                            '日照時數': entry.get('SunshineDuration', {}).get('Total'),
                            '全天空日射量': entry.get('GlobalSolarRadiation', {}).get('Accumulation'),
                            '能見度': entry.get('Visibility', {}).get('Instantaneous'),
                            '總雲量': entry.get('TotalCloudAmount', {}).get('Instantaneous'),
                            '雲冪高': None,
                            '紫外線指數': entry.get('UVIndex', {}).get('Accumulation')
                        }
                        all_data.append(row)
            except Exception as e:
                print(f"錯誤: 測站 {station_id} 檔案 {file_name} 讀取失敗: {e}")

        # 儲存 CSV 到年份資料夾下
        if all_data:
            df = pd.DataFrame(all_data)
            df = df.reindex(columns=target_columns)
            df['觀測時間'] = pd.to_datetime(df['觀測時間'])
            df = df.sort_values(by='觀測時間')
            
            # 檔名維持 測站_年份.csv，但路徑改在年份資料夾內
            output_file = os.path.join(year_output_dir, f"{station_id}_hour.csv")
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
    print(f"--- {year} 年度所有測站處理完成 ---")

print("\n--- 全部批次任務結束 ---")