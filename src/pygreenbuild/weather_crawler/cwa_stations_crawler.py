import pandas as pd
import requests
#from bs4 import BeautifulSoup
import re
import datetime
import os
import io


def cwa_stations(i=0, columns_to_export=None, output_dir=None, new_columns=None):
    # 1. 設定網址和 Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        # 2. 發送請求並取得 HTML 內容
        response = requests.get('https://hdps.cwa.gov.tw/static/state.html', headers=headers)
        response.raise_for_status()
        response.encoding = 'utf-8'
        html_content = response.text

        # --- 抓取日期並格式化  ---
        soup = BeautifulSoup(html_content, 'html.parser')
        date_pattern = re.compile(r'\d{4}/\d{2}/\d{2}')
        date_match_list = soup.find_all(string=date_pattern)

        formatted_date = datetime.date.today().strftime('%Y%m%d')
        extracted_date_str = None

        if date_match_list:
            date_match_full_text = date_match_list[-1]
            date_only_match = re.search(date_pattern, date_match_full_text)
            if date_only_match:
                extracted_date_str = date_only_match.group(0)
                formatted_date = extracted_date_str.replace('/', '')

        # --- 判斷表格索引 i 並決定檔名開頭  ---
        station_prefix = 'cwa_station'

        if i == 0:
            station_prefix = '現有站'
        elif i == 1:
            station_prefix = '撤銷站'

        print(
            f"--- 準備抓取：{station_prefix} (索引 {i}) | 網頁日期: {extracted_date_str if extracted_date_str else formatted_date} ---")

        # 3. 根據站別、日期建立檔案路徑
        base_filename = f'{station_prefix}_{formatted_date}.csv'

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            csv_filepath = os.path.join(output_dir, base_filename)
        else:
            csv_filepath = base_filename

        # --- 讀取表格資料並存檔 ---
        tables = pd.read_html(io.StringIO(html_content))
        target_table_index = i

        if len(tables) > target_table_index:
            df = tables[target_table_index]

            # ⭐ 步驟 A: 處理 DataFrame：新增欄位 (先創建並賦值)
            if new_columns is not None:
                for col_name, col_value in new_columns.items():
                    if col_name in df.columns:
                        print(f"⚠️ 警告：新增欄位名稱 '{col_name}' 與網頁欄位重名，將會被固定值覆蓋！")
                    df[col_name] = col_value
                    print(f"✅ 資料處理 (A): 已新增欄位 '{col_name}'，內容為 '{col_value}'")

            # ⭐ 步驟 B: 處理 DataFrame：選擇欄位和重新命名 (後篩選/改名)
            if columns_to_export is not None:

                # 計算所有有效的欄位名（包含新增的欄位）
                available_cols = list(df.columns)
                valid_columns = {
                    old_col: new_col
                    for old_col, new_col in columns_to_export.items()
                    if old_col in available_cols
                }

                # 檢查新名稱是否重複
                new_names = list(valid_columns.values())
                if len(new_names) != len(set(new_names)):
                    # 提示用戶必須修改他們輸入的 export_cols
                    print(
                        "❌ 致命錯誤：欄位輸出名稱重複！請檢查 columns_to_export 字典，不能有兩個不同的原始欄位改名為同一個新名稱。")
                    print(f"衝突的輸出名稱: {valid_columns}")
                    return  # 終止程式執行

                # 選取欄位
                df = df[list(valid_columns.keys())]

                # 重新命名欄位
                df = df.rename(columns=valid_columns)
                print(f"✅ 資料處理 (B): 已選取並更名為：{list(df.columns)}")

            else:
                print("ℹ️ 資料處理：輸出全部欄位。")

            # 4. 儲存為 CSV 檔案，使用完整路徑
            df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')

            print("✅ 資料已成功儲存。")
            print(f"檔案路徑: **{csv_filepath}**")
        else:
            print(f"❌ 錯誤：網頁中找不到索引為 {target_table_index} 的表格。")

    except requests.exceptions.RequestException as e:
        print(f"❌ 網路連線或請求失敗: {e}")
    except ValueError:
        print("❌ 錯誤：Pandas 無法從網頁內容中找到 HTML 表格。")
    except Exception as e:
        print(f"❌ 發生未知錯誤: {e}")


# 執行函式

# ➊ 定義要新增的欄位和內容 (創建兩個新的欄位)
# new_meta_data = {
#     'startD': '2025-11-01',  # 新增欄位 1
#     'endD': '2025-12-31'  # 新增欄位 2
# }

# # ➋ 定義要匯出的欄位和改名規則 (修正：避免輸出名稱重複)
# export_cols_fixed = {
#     '站號': '站號',  # 網頁欄位為改名，就保持原名
#     # '資料起始日期': '起始日期',         # 網頁欄位改名
#     'startD': '開始日期',  # 新增欄位
#     'endD': '結束日期'  # 新增欄位
# }

# cwa_stations(
#     i=0,
#     columns_to_export=export_cols_fixed,  # 使用修正後的字典
#     new_columns=new_meta_data  # 傳入新增的欄位內容
# )

#cwa_stations()