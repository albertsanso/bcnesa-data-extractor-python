import pdfplumber
import re
from datetime import datetime
import csv
from pathlib import Path

from common import resourceurlsdb
from common import bcnesacommons

def generate_csv_for_season(season):
    season_urls = dict(resourceurlsdb.RESULTSURLS[season])  # Avoid mutating original
    season_urls.pop("base_url", None)

    for competition_key, competition_categories in season_urls.items():
        for category_key, groups in competition_categories.items():
            gen_csv_for_season_competition_category(groups, season.value, competition_key.value, category_key)

def gen_csv_for_season_competition_category(groups, season, competition, category):
    input_folder = Path(bcnesacommons.RESOURCES_FOLDER) / "matches-results/pdf" / str(season) / str(competition) / category
    output_folder = Path(bcnesacommons.RESOURCES_FOLDER) / "matches-results/csv" / str(season) / str(competition) / category

    for group in groups:
        generate_csv_from_pdfs_in_folder(input_folder, output_folder, group)

    pass

def generate_csv_from_pdfs_in_folder(pdf_input_folder, csv_output_folder, group):
    print("--------------------------------")
    #print(pdf_input_folder)
    #print(csv_output_folder)
    #print(group)

    output_filename = "group-{0}-results.csv".format(group["group"])
    output_full_path = csv_output_folder / output_filename
    print(output_full_path)

    input_filename = group["file"]
    input_full_path = pdf_input_folder / input_filename
    results = extract_matches(input_full_path)
    gen_csv_for_file(results, output_full_path)

def gen_csv_for_file(results, csv_output_folder):
    save_to_csv(results, csv_output_folder)

def save_to_csv(data, filename):
    if not data:
        print("No data to save.")
        return

    # Create parent folders if they dont exist
    file_path = Path(filename)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    keys = data[0].keys()
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

def extract_matches(pdf_path):
    matches = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                # skip header lines etc
                if not line:
                    continue
                # Probably only interested in lines with scores: ends with two numbers
                # Let's try to detect lines with a home/away and two numeric scores
                if re.search(r'\d+\s+\d+$', line):
                    parsed = parse_match_line(line)
                    if parsed:
                        matches.append(parsed)
    return matches

def parse_match_line(line):
    """
    Given a line like:
    '28/09/24 17:00 CTT BARCELONA ''A'' CTT ELS AMICS TERRASSA \"A\" 1849 1 5'
    Extract date, time, home team, away team, possibly the match id (1849), and score (1-5).
    """
    # Example regex: date, time, home, away, match_id, home_score, away_score
    line = line.replace('"', '')
    line = line.replace("''", '')
    pattern = re.compile(
        #r'(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2})\s+(.+?)\s+(.+?)\s+(\d+)\s+(\d+)\s+(\d+)'
        r'(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2})\s+(.+?)\s+(\d+)\s+(.+?)\s+(\d)\s+(\d)'
    )
    m = pattern.search(line)
    if not m:
        return None
    date_s, time_s, home, match_id, away, home_score, away_score = m.groups()
    # Clean up team names
    home = clean_whitespace(home)
    away = clean_whitespace(away)
    date_obj = datetime.strptime(date_s + " " + time_s, "%d/%m/%y %H:%M")
    return {
        "date": date_obj,
        "home": home,
        "away": away,
        "match_id": match_id,
        "home_score": int(home_score),
        "away_score": int(away_score),
    }

def clean_whitespace(s):
    return " ".join(s.split())

def main():
    generate_csv_for_season(bcnesacommons.Season.T_2024_2025)
    generate_csv_for_season(bcnesacommons.Season.T_2023_2024)
    generate_csv_for_season(bcnesacommons.Season.T_2022_2023)
    generate_csv_for_season(bcnesacommons.Season.T_2021_2022)
    generate_csv_for_season(bcnesacommons.Season.T_2020_2021)
    generate_csv_for_season(bcnesacommons.Season.T_2019_2020)
    generate_csv_for_season(bcnesacommons.Season.T_2018_2019)

if __name__ == "__main__":
    main()