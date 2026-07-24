"""批次合併 CWA 觀測 JSON → DataFrame / CSV。

預設合併各測站資料夾內全部 ``.json``；可用 ``pattern`` 正則篩選檔名。
"""

from __future__ import annotations

import json
import os
import re
from typing import Dict, Iterable, List, Optional, Pattern, Union

import pandas as pd

from ..transform import json_to_dataframe

_TIME_COLS = ("觀測時間", "觀測月份")


def _list_stations(
    base_path: str, station_ids: Optional[Iterable[str]] = None
) -> List[str]:
    if station_ids is not None:
        return list(station_ids)
    return sorted(
        d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))
    )


def _json_files(
    station_path: str,
    pattern: Optional[Union[str, Pattern[str]]] = None,
) -> List[str]:
    try:
        names = os.listdir(station_path)
    except OSError:
        return []

    rx = re.compile(pattern) if isinstance(pattern, str) else pattern

    selected = []
    for name in names:
        if not name.lower().endswith(".json"):
            continue
        if rx is not None and not rx.search(name):
            continue
        selected.append(name)
    return sorted(selected)


def _load_json(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"預期 JSON 為 list，實際為 {type(data).__name__}: {path}")
    return data


def _sort_time(df: pd.DataFrame) -> pd.DataFrame:
    for col in _TIME_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
            return df.sort_values(by=col).reset_index(drop=True)
    return df


def _merge_station(
    station_path: str,
    pattern: Optional[Union[str, Pattern[str]]] = None,
) -> Optional[pd.DataFrame]:
    frames: List[pd.DataFrame] = []

    for name in _json_files(station_path, pattern):
        path = os.path.join(station_path, name)
        try:
            data = _load_json(path)
        except Exception as exc:
            print(f"讀取失敗 {path}: {exc}")
            continue
        if not data:
            continue
        try:
            frames.append(json_to_dataframe(data))
        except Exception as exc:
            print(f"轉換失敗 {path}: {exc}")
            continue

    if not frames:
        return None

    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(axis=1, how="all")
    return _sort_time(df)


def cwa_merge(
    base_path: str,
    output_dir: Optional[str] = None,
    station_ids: Optional[Iterable[str]] = None,
    pattern: Optional[Union[str, Pattern[str]]] = None,
    to_csv: bool = True,
    csv_name: str = "{station_id}.csv",
) -> Dict[str, pd.DataFrame]:
    """
    批次讀取測站 JSON，經 ``json_to_dataframe`` 轉換後合併。

    Args:
        base_path: 測站根目錄（子資料夾為測站 ID）。
        output_dir: CSV 輸出目錄；``to_csv=True`` 時必填。
        station_ids: 指定測站；預設處理全部子資料夾。
        pattern: 檔名正則（只合併符合者）。``None`` 表示該測站資料夾內全部 ``.json``。
            例：``r"^2020"``、``r"2020|2021"``。
        to_csv: 是否寫出 CSV。
        csv_name: 輸出檔名樣板，可用 ``{station_id}``。

    Returns:
        ``{station_id: DataFrame}``
    """
    if to_csv and not output_dir:
        raise ValueError("to_csv=True 時必須提供 output_dir")

    results: Dict[str, pd.DataFrame] = {}

    for station_id in _list_stations(base_path, station_ids):
        station_path = os.path.join(base_path, station_id)
        df = _merge_station(station_path, pattern)
        if df is None:
            print(f"略過 {station_id}（無符合檔案）")
            continue

        results[station_id] = df

        if to_csv and output_dir:
            os.makedirs(output_dir, exist_ok=True)
            out_path = os.path.join(
                output_dir, csv_name.format(station_id=station_id)
            )
            df.to_csv(out_path, index=False, encoding="utf-8-sig")
            print(f"完成 {station_id}（{len(df)} 列）→ {out_path}")
        else:
            print(f"完成 {station_id}（{len(df)} 列）")

    return results


def cwa_hour_merge(
    base_path: str,
    output_dir: Optional[str] = None,
    station_ids: Optional[Iterable[str]] = None,
    pattern: Optional[Union[str, Pattern[str]]] = None,
    to_csv: bool = True,
) -> Dict[str, pd.DataFrame]:
    """小時資料合併；輸出 ``{station_id}_hour.csv``。"""
    return cwa_merge(
        base_path,
        output_dir=output_dir,
        station_ids=station_ids,
        pattern=pattern,
        to_csv=to_csv,
        csv_name="{station_id}_hour.csv",
    )


def cwa_day_merge(
    base_path: str,
    output_dir: Optional[str] = None,
    station_ids: Optional[Iterable[str]] = None,
    pattern: Optional[Union[str, Pattern[str]]] = None,
    to_csv: bool = True,
) -> Dict[str, pd.DataFrame]:
    """日資料合併；輸出 ``{station_id}.csv``。"""
    return cwa_merge(
        base_path,
        output_dir=output_dir,
        station_ids=station_ids,
        pattern=pattern,
        to_csv=to_csv,
        csv_name="{station_id}.csv",
    )


def cwa_month_merge(
    base_path: str,
    output_dir: Optional[str] = None,
    station_ids: Optional[Iterable[str]] = None,
    pattern: Optional[Union[str, Pattern[str]]] = None,
    to_csv: bool = True,
) -> Dict[str, pd.DataFrame]:
    """月資料合併；輸出 ``{station_id}.csv``。"""
    return cwa_merge(
        base_path,
        output_dir=output_dir,
        station_ids=station_ids,
        pattern=pattern,
        to_csv=to_csv,
        csv_name="{station_id}.csv",
    )
