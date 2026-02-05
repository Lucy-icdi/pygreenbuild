import pandas as pd
import numpy as np
from psychrolib import SetUnitSystem, GetTWetBulbFromRelHum, SI
import time # 引入 time 模組，用於增加延遲
from pathlib import Path

def download_wrf_inside(date_range,wrftype, lat, lon, hh_list):
    all_data_frames = []
    type_map = {
        "3km": "WRF",
        "1km": "WRFv2"
    }
    type = type_map.get(wrftype)
    print(f"--- 開始下載任務 (座標: {lat}, {lon}) ---")
    for single_date in date_range:
        setday = single_date.strftime('%Y-%m-%d')

        for hh in hh_list:   # ⭐ 新增：時間迴圈
            url = (
                f"http://192.168.1.202:8888/data/{type}?st={setday}T{hh}%3A00"
                f"&ed={setday}T{hh}%3A00&lat={lat}&lon={lon}"
                f"&parameters=ALL&forecast_hours=0%2C48&time_zone=LT"
            )
            try:
                dt = pd.read_csv(url)
                all_data_frames.append(dt)
                print(f"✅ 成功讀取: {setday} {hh}:00")
                time.sleep(5)

            except Exception as e:
                print(f"❌ 讀取失敗: {setday} {hh}:00 → {e}")

    if all_data_frames:
        allDT = pd.concat(all_data_frames, ignore_index=True)
        allDT['WS'] = np.sqrt(allDT['U'] ** 2 + allDT['V'] ** 2).round(2)

        # 3. 計算風向
        angle_rad = np.arctan2(allDT['V'], allDT['U'])
        angle_deg = np.degrees(angle_rad)
        allDT['WD'] = np.round(((270 - angle_deg) % 360), 0)

        # 4. 計算濕球溫度
        SetUnitSystem(SI)
        allDT['fc_wet'] = allDT.apply(
            lambda row: GetTWetBulbFromRelHum(
                row['T'],
                row['RH'] / 100,
                row['P'] * 100), axis=1).round(2)

        # 5. 欄位整理與重新命名
        allDT = allDT.drop(['filename', 'flag',  'U', 'V'], axis=1)
        allDT.columns = ['mtime', 'ftime', 'fc_P', 'fc_Precp', 'fc_T',
                          'fc_DPT', 'fc_SH', 'fc_RH', 'fc_SKT', 'fc_NSWRF',
                          'fc_PMSL','lat', 'lon', 'fc_WS', 'fc_WD', 'fc_wet']

        cols = [col for col in allDT.columns if col not in ['lat', 'lon']] + ['lat', 'lon']
        allDT = allDT[cols]

        #確保 mtime 和 ftime 是 pandas 的 datetime 物件，這樣 to_sql 會正確處理
        allDT['mtime'] = pd.to_datetime(allDT['mtime'])
        allDT['ftime'] = pd.to_datetime(allDT['ftime'])

        print(f"--- 下載完成，共 {len(all_data_frames)} 份資料 ---")
        return allDT

    else:
        print("⚠️ 沒有任何資料被成功下載")
        return pd.DataFrame()

