"""codis_merge 單元測試（暫存 JSON，不依賴本機 F: 路徑）。"""

from __future__ import annotations

import json
from pathlib import Path

from pygreenbuild.load import codis_hour_merge, codis_merge


def _write_hour_json(path: Path, times: list[str]) -> None:
    rows = [
        {
            "DataTime": t,
            "AirTemperature": {"Instantaneous": 20.0 + i},
            "StationPressure": {"Instantaneous": 1010.0},
        }
        for i, t in enumerate(times)
    ]
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")


def test_codis_merge_all_json_in_station_folder(tmp_path: Path) -> None:
    station = tmp_path / "stations" / "466920"
    station.mkdir(parents=True)
    _write_hour_json(station / "20200101_466920.json", ["2020-01-01T01:00:00"])
    _write_hour_json(station / "20210101_466920.json", ["2021-01-01T01:00:00"])

    out = tmp_path / "out"
    dfs = codis_merge(str(tmp_path / "stations"), output_dir=str(out), to_csv=True)

    assert "466920" in dfs
    assert len(dfs["466920"]) == 2
    assert (out / "466920.csv").exists()


def test_codis_merge_pattern_filters_files(tmp_path: Path) -> None:
    station = tmp_path / "stations" / "466920"
    station.mkdir(parents=True)
    _write_hour_json(station / "20200101_466920.json", ["2020-01-01T01:00:00"])
    _write_hour_json(station / "20210101_466920.json", ["2021-01-01T01:00:00"])

    dfs = codis_merge(
        str(tmp_path / "stations"),
        pattern=r"^2020",
        to_csv=False,
    )

    assert len(dfs["466920"]) == 1
    assert str(dfs["466920"]["觀測時間"].iloc[0]).startswith("2020")


def test_codis_hour_merge_csv_name(tmp_path: Path) -> None:
    station = tmp_path / "stations" / "466920"
    station.mkdir(parents=True)
    _write_hour_json(station / "20200101_466920.json", ["2020-01-01T01:00:00"])

    out = tmp_path / "out"
    codis_hour_merge(str(tmp_path / "stations"), output_dir=str(out), to_csv=True)

    assert (out / "466920_hour.csv").exists()
