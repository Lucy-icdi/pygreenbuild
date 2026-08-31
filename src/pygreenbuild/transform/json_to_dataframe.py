"""將中央氣象署（CWA）CODIS 觀測 JSON 轉成中文欄位 DataFrame。"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import pandas as pd
from pandas import json_normalize

from pygreenbuild.transform.transform_time import _roll_past_2359_series

_CWA_HOUR_MAPPING: dict[str, str | None] = {
    "觀測時間": "DataTime",
    "測站氣壓": "StationPressure.Instantaneous",
    "海平面氣壓": "SeaLevelPressure.Instantaneous",
    "氣溫": "AirTemperature.Instantaneous",
    "濕球溫度": None,
    "露點溫度": "DewPointTemperature.Instantaneous",
    "相對溼度": "RelativeHumidity.Instantaneous",
    "風速": "WindSpeed.Mean",
    "風向": "WindDirection.Mean",
    "十分鐘平均風速": "WindSpeed.TenMinutelyMaximum",
    "十分鐘平均風向": "WindDirection.TenMinutelyMaximum",
    "最大瞬間風風速": "PeakGust.Maximum",
    "最大瞬間風風向": "PeakGust.Direction",
    "降水量": "Precipitation.Accumulation",
    "降水時數": "PrecipitationDuration.Total",
    "日照時數": "SunshineDuration.Total",
    "全天空日射量": "GlobalSolarRadiation.Accumulation",
    "能見度": "Visibility.Instantaneous",
    "總雲量": "TotalCloudAmount.Instantaneous",
    "雲冪高": None,
    "紫外線指數": "UVIndex.Accumulation",
}

_CWA_DAY_MAPPING: dict[str, str | None] = {
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

_CWA_MONTH_MAPPING: dict[str, str | None] = {
    "觀測月份": "DataYearMonth",
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
    "風速": "WindSpeed.Mean",
    "風向": "WindDirection.Prevailing",
    "最大瞬間風": "PeakGust.Maximum",
    "最大瞬間風風向": "PeakGust.Direction",
    "最大瞬間風風速時間": "PeakGust.MaximumTime",
    "降水量": "Precipitation.Accumulation",
    "降水時數": "PrecipitationDuration.Total",
    "降水日數": "Precipitation.PrecipitationDays",
    "最大十分鐘降水量": "Precipitation.TenMinutelyMaximum",
    "最大十分鐘降水量起始時間": "Precipitation.TenMinutelyMaximumTime",
    "最大六十分鐘降水量": "Precipitation.SixtyMinutelyMaximum",
    "最大六十分鐘降水量起始時間": "Precipitation.SixtyMinutelyMaximumTime",
    "最大日降水量": "Precipitation.DailyMaximum",
    "最大日降水量時間": "Precipitation.DailyMaximumDate",
    "相對溼度": "RelativeHumidity.Mean",
    "A型蒸發量": "EvaporationClassAPan.Accumulation",
    "日照時數": "SunshineDuration.Total",
    "全天空日射量": "GlobalSolarRadiation.Accumulation",
    "平均日最高紫外線指數": "UVIndex.MeanDailyMaximum",
    "月最高紫外線指數": "UVIndex.Maximum",
    "月最高紫外線指數時間": "UVIndex.MaximumTime",
    "總雲量_衛星": "TotalCloudAmount.SatRetrievedMean",
    "地溫0cm": "SoilTemperatureAt0cm.Mean",
    "地溫5cm": "SoilTemperatureAt5cm.Mean",
    "地溫10cm": "SoilTemperatureAt10cm.Mean",
    "地溫20cm": "SoilTemperatureAt20cm.Mean",
    "地溫30cm": "SoilTemperatureAt30cm.Mean",
    "地溫50cm": "SoilTemperatureAt50cm.Mean",
    "地溫100cm": "SoilTemperatureAt100cm.Mean",
}

_NA_VALUES: list[object] = [
    "",
    "NULL",
    "null",
    "NaN",
    "-99",
    "-99.0",
    "-99.9",
    "-99.5",
    "-99.95",
    "-999",
    "-999.0",
    "-999.5",
    "-999.9",
    -99,
    -99.0,
    -99.9,
    -99.5,
    -99.95,
    -999,
    -999.0,
    -999.5,
    -999.9,
    "x",
    "&",
    "V",
    "/",
    "--",
]

_TIME_COL = "觀測時間"
_PRECIPITATION_COL = "降水量"

_TEMP_COLUMNS_LT_MINUS_50: set[str] = {
    "露點溫度",
    "濕球溫度",
    "氣溫",
    "最高氣溫",
    "最低氣溫",
    "地溫0cm",
    "地溫5cm",
    "地溫10cm",
    "地溫20cm",
    "地溫30cm",
    "地溫50cm",
    "地溫100cm",
}


def _detect_mapping(data: Sequence[Mapping[str, Any]]) -> dict[str, str | None]:
    """依 JSON 鍵自動選擇小時／日／月欄位對應表。"""
    if not data:
        raise ValueError("資料為空")

    sample = data[0]

    if "DataTime" in sample:
        return _CWA_HOUR_MAPPING

    if "DataDate" in sample:
        return _CWA_DAY_MAPPING

    if "DataYearMonth" in sample:
        return _CWA_MONTH_MAPPING

    raise ValueError("未知資料格式")


def _adjust_observation_time(df: pd.DataFrame) -> pd.DataFrame:
    """``觀測時間`` 為 ``23:59:00``–``23:59:59`` 時改為隔天 ``00:00:00``。"""
    if _TIME_COL not in df.columns:
        return df

    rolled = _roll_past_2359_series(df[_TIME_COL])
    df[_TIME_COL] = rolled.dt.strftime("%Y-%m-%dT%H:%M:%S")
    return df


def _is_time_column(col: str) -> bool:
    """判斷是否為時間類欄位（清理數值時略過）。"""
    return col == _TIME_COL or col == "觀測月份" or col.endswith("時間")


def _mask_below_threshold(df: pd.DataFrame, col: str, threshold: float) -> None:
    """將可轉數值且小於 ``threshold`` 的儲存格設為 ``pd.NA``。"""
    numeric = pd.to_numeric(df[col], errors="coerce")
    df.loc[numeric < threshold, col] = pd.NA


def _clean_values(df: pd.DataFrame) -> pd.DataFrame:
    """套用缺值代碼替換、微量降水 ``T``→0.4，以及不合理數值遮罩。"""
    if _PRECIPITATION_COL in df.columns:
        df[_PRECIPITATION_COL] = df[_PRECIPITATION_COL].replace("T", 0.4)

    df = df.replace(_NA_VALUES, pd.NA)

    for col in df.columns:
        if _is_time_column(col):
            continue
        if col in _TEMP_COLUMNS_LT_MINUS_50:
            _mask_below_threshold(df, col, -50)
        else:
            _mask_below_threshold(df, col, 0)

    return df


def _unify_missing(df: pd.DataFrame) -> pd.DataFrame:
    """將 ``NaN``／``None`` 等統一為 pandas 系統遺失值 ``pd.NA``。

    透過 ``convert_dtypes()`` 轉成 nullable 型別，顯示為 ``<NA>``，
    與浮點 ``nan`` 區隔並利於後續缺值判斷。
    """
    return df.convert_dtypes()


def json_to_dataframe(
    data: Sequence[Mapping[str, Any]],
    column_mapping: Mapping[str, str | None] | None = None,
) -> pd.DataFrame:
    """將 CWA／CODIS 觀測 JSON（list of dict）轉成中文欄位 DataFrame。

    依第一筆資料的鍵自動辨識格式：

    - 含 ``DataTime`` → 小時報（``_CWA_HOUR_MAPPING``）
    - 含 ``DataDate`` → 日報（``_CWA_DAY_MAPPING``）
    - 含 ``DataYearMonth`` → 月報（``_CWA_MONTH_MAPPING``）

    亦可自行傳入 ``column_mapping``（中文欄名 → JSON 扁平路徑；``None`` 表示該欄恒為空）。

    轉換後會：

    - 將 ``觀測時間`` 為 ``23:59:00``–``23:59:59`` 者改為隔天 ``00:00:00``
    - 降水量 ``"T"``（微量）改為 ``0.4``
    - 常見缺測代碼（如 ``-99``、``"x"``）改為 ``NA``
    - 溫度相關欄小於 ``-50``、其餘非時間數值欄小於 ``0`` 改為 ``NA``
    - 將 ``NaN``／``None`` 統一為系統遺失值 ``pd.NA``（顯示 ``<NA>``）
    - 刪除整欄皆為空值的欄位

    Parameters
    ----------
    data :
        觀測紀錄列表，每筆為巢狀或已扁平化的 dict（單位：不適用）。
    column_mapping :
        中文欄名到 JSON 路徑的對應；``None``（預設）則自動偵測（單位：不適用）。
        路徑值為 ``None`` 時該欄填入空值（最終會因整欄空白而被刪除）。

    Returns
    -------
    pd.DataFrame
        中文欄位觀測表（已去掉整欄空白欄）。時間欄以字串
        ``YYYY-MM-DDTHH:MM:SS`` 表示（若有 ``觀測時間``）；缺測統一為
        ``pd.NA``（單位：依欄位而定）。

    Raises
    ------
    ValueError
        ``data`` 為空，或無法辨識為小時／日／月格式（且未提供 ``column_mapping``）。
    """
    if column_mapping is None:
        column_mapping = _detect_mapping(data)

    df = json_normalize(data)

    df_selected = pd.DataFrame()

    for col_name, json_path in column_mapping.items():
        if json_path is not None and json_path in df.columns:
            df_selected[col_name] = df[json_path]
        else:
            df_selected[col_name] = pd.NA

    df_selected = _adjust_observation_time(df_selected)
    df_selected = _clean_values(df_selected)
    df_selected = _unify_missing(df_selected)

    return df_selected.dropna(axis=1, how="all")
