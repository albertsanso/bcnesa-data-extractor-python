from pathlib import Path
import sys
import urllib.request

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from common import bcnesacommons
from common import resourceurlsdb

RESOURCES_DIR = ROOT_DIR / "resources"


def download_for_season(season):
    url_for_season = resourceurlsdb.get_played_matches_url_for_season(season)
    file_path = RESOURCES_DIR / "played-matches" / season.value / "played-matches.pdf"

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading: {url_for_season}")
        urllib.request.urlretrieve(url_for_season, file_path)
        print(f"  -> {file_path} ({file_path.stat().st_size} bytes)")
    except Exception as e:
        print(f"Error downloading {url_for_season} to {file_path}: {e}")


def main():
    download_for_season(bcnesacommons.Season.T_2025_2026)
    download_for_season(bcnesacommons.Season.T_2024_2025)
    download_for_season(bcnesacommons.Season.T_2023_2024)
    download_for_season(bcnesacommons.Season.T_2022_2023)
    download_for_season(bcnesacommons.Season.T_2021_2022)
    download_for_season(bcnesacommons.Season.T_2020_2021)
    download_for_season(bcnesacommons.Season.T_2019_2020)
    download_for_season(bcnesacommons.Season.T_2018_2019)


if __name__ == "__main__":
    main()