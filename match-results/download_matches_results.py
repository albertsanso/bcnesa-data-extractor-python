from pathlib import Path
import urllib.request
import traceback

from common import resourceurlsdb
from common import bcnesacommons

def download_for_season(season):
    season_urls = dict(resourceurlsdb.RESULTSURLS[season])  # Avoid mutating original
    base_url_for_season = season_urls.pop("base_url", None)

    for competition_key, competition_categories in season_urls.items():
        for category_key, groups in competition_categories.items():
            folder = Path(bcnesacommons.RESOURCES_FOLDER) / "matches-results/pdf" / str(season.value) / str(competition_key.value) / category_key

            for group in groups:
                download_group_pdf(base_url_for_season, folder, group)

def download_group_pdf(base_url, folder, group):
    try:
        group_pdffile = group["file"]
        final_url = f"{base_url}/{group_pdffile}"
        file_path = Path(folder) / group_pdffile

        file_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Downloading: {final_url}")
        urllib.request.urlretrieve(final_url, file_path)

    except Exception as e:
        print(f"Error downloading {final_url} to {file_path}")
        print(traceback.format_exc())

def main():
    download_for_season(bcnesacommons.Season.T_2024_2025)
    download_for_season(bcnesacommons.Season.T_2023_2024)
    download_for_season(bcnesacommons.Season.T_2022_2023)
    download_for_season(bcnesacommons.Season.T_2021_2022)
    download_for_season(bcnesacommons.Season.T_2020_2021)
    download_for_season(bcnesacommons.Season.T_2019_2020)
    download_for_season(bcnesacommons.Season.T_2018_2019)

if __name__ == "__main__":
    main()