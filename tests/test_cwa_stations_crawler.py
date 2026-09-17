"""cwa_stations 單元測試（mock 網路與 read_html，不打真實網頁）。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from pygreenbuild.ingestion.weather_crawler.cwa_stations_crawler import cwa_stations

MODULE = "pygreenbuild.ingestion.weather_crawler.cwa_stations_crawler"

SAMPLE_HTML = """
<html><body>
<p>更新：2024/11/15</p>
<table>
  <tr><th>站號</th><th>站名</th></tr>
  <tr><td>466920</td><td>臺北</td></tr>
</table>
<table>
  <tr><th>站號</th><th>站名</th></tr>
  <tr><td>467770</td><td>舊站</td></tr>
</table>
</body></html>
"""


def _mock_response() -> MagicMock:
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.encoding = "utf-8"
    response.text = SAMPLE_HTML
    return response


class TestCwaStationsOutputPath:
    @patch(f"{MODULE}.pd.read_html")
    @patch(f"{MODULE}.requests.get")
    def test_saves_to_dir_with_default_filename(
        self, mock_get: MagicMock, mock_read_html: MagicMock, tmp_path: Path
    ) -> None:
        mock_get.return_value = _mock_response()
        mock_read_html.return_value = [
            pd.DataFrame({"站號": ["466920"], "站名": ["臺北"]}),
            pd.DataFrame({"站號": ["467770"], "站名": ["舊站"]}),
        ]

        cwa_stations(open=True, output=str(tmp_path))

        out = tmp_path / "現有站_20241115.csv"
        assert out.exists()
        df = pd.read_csv(out, encoding="utf-8-sig")
        assert list(df["站號"]) == [466920]

    @patch(f"{MODULE}.pd.read_html")
    @patch(f"{MODULE}.requests.get")
    def test_saves_with_custom_filepath(
        self, mock_get: MagicMock, mock_read_html: MagicMock, tmp_path: Path
    ) -> None:
        mock_get.return_value = _mock_response()
        mock_read_html.return_value = [
            pd.DataFrame({"站號": ["466920"], "站名": ["臺北"]}),
            pd.DataFrame({"站號": ["467770"], "站名": ["舊站"]}),
        ]
        custom = tmp_path / "data" / "stn.csv"

        cwa_stations(open=True, output=str(custom))

        assert custom.exists()
        assert not (tmp_path / "data" / "現有站_20241115.csv").exists()
        df = pd.read_csv(custom, encoding="utf-8-sig")
        assert list(df["站名"]) == ["臺北"]

    @patch(f"{MODULE}.pd.read_html")
    @patch(f"{MODULE}.requests.get")
    def test_saves_with_bare_custom_filename(
        self,
        mock_get: MagicMock,
        mock_read_html: MagicMock,
        tmp_path: Path,
        monkeypatch,
    ) -> None:
        mock_get.return_value = _mock_response()
        mock_read_html.return_value = [
            pd.DataFrame({"站號": ["466920"], "站名": ["臺北"]}),
            pd.DataFrame({"站號": ["467770"], "站名": ["舊站"]}),
        ]
        monkeypatch.chdir(tmp_path)

        cwa_stations(open=True, output="stn.csv")

        out = tmp_path / "stn.csv"
        assert out.exists()
        assert not (tmp_path / "現有站_20241115.csv").exists()

    @patch(f"{MODULE}.pd.read_html")
    @patch(f"{MODULE}.requests.get")
    def test_closed_stations_default_filename(
        self, mock_get: MagicMock, mock_read_html: MagicMock, tmp_path: Path
    ) -> None:
        mock_get.return_value = _mock_response()
        mock_read_html.return_value = [
            pd.DataFrame({"站號": ["466920"], "站名": ["臺北"]}),
            pd.DataFrame({"站號": ["467770"], "站名": ["舊站"]}),
        ]

        cwa_stations(open=False, output=str(tmp_path))

        out = tmp_path / "撤銷站_20241115.csv"
        assert out.exists()
        df = pd.read_csv(out, encoding="utf-8-sig")
        assert list(df["站號"]) == [467770]
