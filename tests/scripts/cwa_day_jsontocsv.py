import os
import json
import pandas as pd
import numpy as np
from pandas import json_normalize

# === 設定區 ===
base_path = r"F:/BackUp/CODis/cwa_monthly_data/現有站"
output_base = r"F:/BackUp/CODis/json轉csv/day"
years = ['2020','2021','2022', '2023']

# === 欄位 mapping（中文 → JSON path）===
column_mapping = {
    "觀測時間": "DataDate",
    "測站氣壓": "StationPressure.Mean",
    "海平面氣壓": "SeaLevelPressure.Mean",
    "測站最高氣壓": "StationPressure.Maximum",
    "測站最高氣壓時間": "StationPressure.MaximumTime",
    "測站最低氣壓": "StationPressure.Minimum",
    "測站最低氣壓時間": "StationPressure.MinimumTime",
    "氣溫": "AirTemperature.Mean",
    "最高氣溫": "AirTemperature.Maximum",
    "最高氣溫時間": "AirTemperature.MaximumTime",
    "最低氣溫": "AirTemperature.Minimum",
    "最低氣溫時間": "AirTemperature.MinimumTime",
    "露點溫度": "DewPointTemperature.Mean",
    "相對溼度": "RelativeHumidity.Mean",
    "最小相對溼度": "RelativeHumidity.Minimum",
    "最小相對溼度時間": "RelativeHumidity.MinimumTime",
    "風速": "WindSpeed.Mean",
    "風向": "WindDirection.Prevailing",
    "最大瞬間風": "PeakGust.Maximum",
    "最大瞬間風風向": "PeakGust.Direction",
    "最大瞬間風風速時間": "PeakGust.MaximumTime",
    "降水量": "Precipitation.Accumulation",
    "降水時數": "PrecipitationDuration.Total",
    "最大十分鐘降水量": "Precipitation.TenMinutelyMaximum",
    "最大十分鐘降水量起始時間": "Precipitation.TenMinutelyMaximumTime",
    "最大六十分鐘降水量": "Precipitation.SixtyMinutelyMaximum",
    "最大六十分鐘降水量起始時間": "Precipitation.SixtyMinutelyMaximumTime",
    "日照時數": "SunshineDuration.Total",
    "日照率": "SunshineDuration.Rate",
    "全天空日射量": "GlobalSolarRadiation.Accumulation",
    "能見度_自動": "Visibility.AutoMean",
    "A型蒸發量": "EvaporationClassAPan.Accumulation",
    "日最高紫外線指數": "UVIndex.Maximum",
    "日最高紫外線指數時間": "UVIndex.MaximumTime",
    "總雲量_衛星": "TotalCloudAmount.SatRetrievedMean",
    "地溫0cm": "SoilTemperatureAt0cm.Mean",
    "地溫5cm": "SoilTemperatureAt5cm.Mean",
    "地溫10cm": "SoilTemperatureAt10cm.Mean",
    "地溫20cm": "SoilTemperatureAt20cm.Mean",
    "地溫30cm": "SoilTemperatureAt30cm.Mean",
    "地溫50cm": "SoilTemperatureAt50cm.Mean",
    "地溫100cm": "SoilTemperatureAt100cm.Mean",
}

invalid_values = [None, -99, -999, -99.0, -999.0]

# === 找所有測站 ===
all_stations = [
    d for d in os.listdir(base_path)
    if os.path.isdir(os.path.join(base_path, d))
]

# === 主流程 ===
for station_id in all_stations:
    station_path = os.path.join(base_path, station_id)

    for year in years:

        print(f"處理 {station_id} - {year}")

        all_df = []

        # === 找該測站該年份所有 JSON ===
        for file in os.listdir(station_path):
            if file.endswith(".json") and file.startswith(year):
                file_path = os.path.join(station_path, file)

                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                df = json_normalize(data)

                # === 欄位轉換 ===
                df_selected = pd.DataFrame()
                for col_name, json_path in column_mapping.items():
                    if json_path in df.columns:
                        df_selected[col_name] = df[json_path]
                    else:
                        df_selected[col_name] = np.nan

                all_df.append(df_selected)

        # === 沒資料就跳過 ===
        if not all_df:
            continue

        # === 合併全年 並刪除整欄無效值 ===
        df_year = pd.concat(all_df, ignore_index=True)
        df_year = df_year.replace(invalid_values, pd.NA)
        df_year = df_year.dropna(axis=1, how='all')

        # === 排序 ===
        df_year['觀測時間'] = pd.to_datetime(df_year['觀測時間'])
        df_year = df_year.sort_values(by='觀測時間')


        # === 建立輸出資料夾 ===
        year_output_dir = os.path.join(output_base, year)
        os.makedirs(year_output_dir, exist_ok=True)

        # === 輸出 ===
        output_file = os.path.join(year_output_dir, f"{station_id}.csv")
        df_year.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"完成 {station_id} {year}")