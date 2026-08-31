#source("scripts/python_functions.R")
library(reticulate)

# 將 Python pandas.DataFrame 轉成 R data.frame，供 head()／View()／dplyr 使用
.py_df_to_r <- function(df) {
  as.data.frame(py_to_r(df), stringsAsFactors = FALSE)
}

# 下載 CODIS 年資料
codis_yearly <- import("pygreenbuild.ingestion.weather_crawler.codis_crawler_tojson")$codis_yearly

# 下載 CODIS 月資料
codis_monthly <- import("pygreenbuild.ingestion.weather_crawler.codis_crawler_tojson")$codis_monthly

# 下載 CODIS 日資料
codis_daily <- import("pygreenbuild.ingestion.weather_crawler.codis_crawler_tojson")$codis_daily

# 下載鄉鎮天氣預報－未來 3 天（未指定縣市則批次下載 22 個縣市）
cwa_township_forecast_3day <- import("pygreenbuild.ingestion.weather_crawler.cwa_township_forecast")$cwa_township_forecast_3day

# 下載鄉鎮天氣預報－未來 1 週（可用縣市名稱或資料編號指定）
cwa_township_forecast_week <- import("pygreenbuild.ingestion.weather_crawler.cwa_township_forecast")$cwa_township_forecast_week

# 補齊時間間隔缺口
.fill_time_gaps_py <- import("pygreenbuild.transform.fill_time_gaps")$fill_time_gaps
fill_time_gaps <- function(...) .py_df_to_r(.fill_time_gaps_py(...))

# 將 JSON 轉為 DataFrame（回傳 R data.frame）
.json_to_dataframe_py <- import("pygreenbuild.transform.json_to_dataframe")$json_to_dataframe
json_to_dataframe <- function(...) .py_df_to_r(.json_to_dataframe_py(...))

# 將欄位轉為日期格式（可選 as_string=TRUE 輸出字串）
.to_date_column_py <- import("pygreenbuild.transform.transform_time")$to_date_column
to_date_column <- function(...) .py_df_to_r(.to_date_column_py(...))

# 將欄位轉為時間格式（23:59:00–23:59:59 → 00:00:00；可選 as_string=TRUE）
.to_time_column_py <- import("pygreenbuild.transform.transform_time")$to_time_column
to_time_column <- function(...) .py_df_to_r(.to_time_column_py(...))

# 將欄位轉為日期時間格式（23:59:00–23:59:59 → 隔天 00:00:00；可選 as_string=TRUE）
.to_datetime_column_py <- import("pygreenbuild.transform.transform_time")$to_datetime_column
to_datetime_column <- function(...) .py_df_to_r(.to_datetime_column_py(...))

# PMV 計算（ISO 7730）
pmv_iso <- import("pygreenbuild.transform.pmv")$pmv_iso

# PMV 計算（ASHRAE）
pmv_ashrae <- import("pygreenbuild.transform.pmv")$pmv_ashrae

# 合併 CODIS 資料
.codis_merge_py <- import("pygreenbuild.load.codis_data_merge")$codis_merge
codis_merge <- function(...) .py_df_to_r(.codis_merge_py(...))

# 合併 CODIS 日資料
.codis_day_merge_py <- import("pygreenbuild.load.codis_data_merge")$codis_day_merge
codis_day_merge <- function(...) .py_df_to_r(.codis_day_merge_py(...))

# 合併 CODIS 小時資料
.codis_hour_merge_py <- import("pygreenbuild.load.codis_data_merge")$codis_hour_merge
codis_hour_merge <- function(...) .py_df_to_r(.codis_hour_merge_py(...))

# 合併 CODIS 月資料
.codis_month_merge_py <- import("pygreenbuild.load.codis_data_merge")$codis_month_merge
codis_month_merge <- function(...) .py_df_to_r(.codis_month_merge_py(...))

# 計算冷卻系統 USRT
calculatorUSRT <- import("pygreenbuild.metrics.chiller_usrt")$calculatorUSRT

# 計算冷卻系統性能指標
ChillerKPI <- import("pygreenbuild.metrics.chiller_performance")$ChillerKPI

# 連線資料庫、依範圍查表並填補孤立 NA（回傳 Python dict，含 records）
fill_sql_table_na <- import("pygreenbuild.ingestion.ems_db.factory_db")$fill_sql_table_na

# 填補 DataFrame 的孤立 NA，回傳新的完整 data.frame
.fill_dataframe_na_py <- import("pygreenbuild.transform.fill_dataframe_na")$fill_dataframe_na
fill_dataframe_na <- function(...) .py_df_to_r(.fill_dataframe_na_py(...))

# 將填補結果寫回資料庫，或 sql_only=TRUE 只輸出 SQL 檔
apply_filled_na <- import("pygreenbuild.load.apply_filled_na")$apply_filled_na
