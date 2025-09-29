import pdfplumber
import re
import csv
from pathlib import Path
import traceback
import os

from common import bcnesacommons
from common import resourceurlsdb


def generate_csv_for_season(season):
    competitions = resourceurlsdb.get_competitions_keys_for_season(season)
    for competition_key in competitions:
        competition = resourceurlsdb.get_competition_for_season_and_key(season, competition_key)
        competition_categories = competition["categories"]
        competition_match_days_count = competition["match_days"]
        for category_key, groups in competition_categories.items():
            gen_csv_for_season_competition_category(groups, season.value, competition_key.value, category_key, competition_match_days_count)
            #break
        #break

def gen_csv_for_season_competition_category(groups, season, competition, category, days):
    input_folder = Path(bcnesacommons.RESOURCES_FOLDER) / "matches-results-details/pdf" / str(season) / str(competition) / category
    output_folder = Path(bcnesacommons.RESOURCES_FOLDER) / "matches-results-details/csv" / str(season) / str(competition) / category

    for group in groups:
        generate_csv_from_pdfs_in_folder(input_folder, output_folder, group, days, season)
        #break

def generate_csv_from_pdfs_in_folder(pdf_input_folder, csv_output_folder, group, days, season):

    for jornada in range(1, days+1):

        input_filename = "jornada{0}-g{1}.pdf".format(jornada, group["group"])
        input_full_path = pdf_input_folder / input_filename
        #print("I: " / input_full_path)

        output_filename = "jornada{0}-g{1}.csv".format(jornada, group["group"])
        output_full_path = csv_output_folder / output_filename
        #print("O: " / output_full_path)

        if os.path.exists(input_full_path):
            results_details = extract_matches_details(input_full_path, season)
            #print(results_details)

            plain_results = gen_plain_results(results_details)
            save_to_csv(plain_results, output_full_path)
            #break

def gen_plain_results(jsonresults):
    csvresults = []

    try:
        for jsonrow in jsonresults:

            abc_team = list(filter(lambda x : x["letters"]=="ABC", jsonrow["teams_info"]))[0]["name"]
            xyz_team = list(filter(lambda x : x["letters"]=="XYZ", jsonrow["teams_info"]))[0]["name"]

            print(abc_team + " --- " +xyz_team)

            for single_match_row in jsonrow["single_matches"]:
                plainrow = {}
                abc_player = list(filter(lambda x: x["letter"] in ["A", "B", "C"],single_match_row.values()))[0]
                xyz_player = list(filter(lambda x: x["letter"] in ["X", "Y", "Z"], single_match_row.values()))[0]

                plainrow["abc_team"] = abc_team
                plainrow["xyz_team"] = xyz_team

                plainrow["abc_player_letter"] = abc_player["letter"]
                plainrow["abc_player_license"] = abc_player["license"]
                plainrow["abc_player_name"] = abc_player["name"]
                plainrow["abc_player_score"] = abc_player["score"]

                plainrow["xyz_player_letter"] = xyz_player["letter"]
                plainrow["xyz_player_license"] = xyz_player["license"]
                plainrow["xyz_player_name"] = xyz_player["name"]
                plainrow["xyz_player_score"] = xyz_player["score"]

                csvresults.append(plainrow)

    except Exception as e:
        print(traceback.format_exc())

    return csvresults

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

def extract_matches_details(pdf_path, season):
    matches = []
    if os.path.exists(pdf_path):
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                match = {}
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split("\n")

                match = fill_match_info(get_header_lines(lines, season))
                match_results_lines = get_body_lines(lines, season)
                for line in match_results_lines:
                    line = line.strip()
                    #print(line)
                    if not line:
                        continue
                    if re.search(r'\d+\s+\d+$', line):
                        parsed_line = parse_match_line(line)
                        if parsed_line:
                            if "single_match_result" in parsed_line.keys():
                                if "single_matches" not in match.keys():
                                    match["single_matches"] = []
                                match["single_matches"].append(parsed_line["single_match_result"])
                            elif "match_score" in parsed_line.keys():
                                match["match_score"] = parsed_line["match_score"]
                matches.append(match)
    return matches

def get_header_lines(all_lines, season):
    if season == bcnesacommons.Season.T_2019_2020.value:
        return all_lines[:5]
    else:
        return all_lines[:6]

def get_body_lines(all_lines, season):
    return all_lines[6:]

def fill_match_info(lines):
    match_acta_teams = lines[-1]  # ABC CTT CASTELLGALÍ XYZ CTT LA POBLA DE LILLET

    teams_pattern_string = r'(ABC|XYZ+)\s+(.*?)\s+(ABC|XYZ+)\s+(.*)'
    teams_matches_pattern = re.compile(teams_pattern_string)
    teams_match = teams_matches_pattern.search(match_acta_teams)
    a,b,c,d = teams_match.groups()
    if teams_match:
        return { "teams_info": [ {"letters": a, "name": b}, {"letters": c, "name": d} ] }
    else:
        return {}

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
        #r'^([A-Z]) (\d+) ([A-Za-zÁÉÍÓÚÜÑÀÈÌÒÙÇ]+ [A-Za-zÁÉÍÓÚÜÑàèìòùç]+) ([A-Z]) (\d+) ([A-Za-zÁÉÍÓÚÜÑÀÈÌÒÙÇ]+ [A-Za-zÁÉÍÓÚÜÑàèìòùç]+) (\d+) (\d+)$'
        r'^([ABCXYZ]) (\d+) (\b(?:\w+\s+){1,2}\w+\b) ([ABCXYZ]) (\d+) (\b(?:\w+\s+){1,2}\w+\b) (\d+) (\d+)$'
    )
    matches1 = pattern.search(line)
    if not matches1:
        pattern = re.compile(r'^(\d) (\d)$')
        matches2 = pattern.search(line)
        if matches2:
            score_team_1, score_team_2 = matches2.groups()
            return {
                "match_score": {
                    "score_team_ABC": score_team_1,
                    "score_team_XYZ": score_team_2
                }
            }
        return None

    the_matched_groups = matches1.groups()
    #date_s, time_s, home, match_id, away, home_score, away_score = m.groups()
    letter_player_1, license_player_1, name_player_1, letter_player_2, license_player_2, name_player_2, score_player_1, score_player_2 = matches1.groups()
    pass
    # Clean up team names

    return {
        "single_match_result": {
            "player_1": {
                "letter": letter_player_1,
                "license": license_player_1,
                "name": name_player_1,
                "score": score_player_1
            },
            "player_2": {
                "letter": letter_player_2,
                "license": license_player_2,
                "name": name_player_2,
                "score": score_player_2
            }
        }
    }

def clean_whitespace(s):
    return " ".join(s.split())

def main():
    #generate_csv_for_season(bcnesacommons.Season.T_2024_2025)
    #generate_csv_for_season(bcnesacommons.Season.T_2023_2024)
    #generate_csv_for_season(bcnesacommons.Season.T_2022_2023)
    #generate_csv_for_season(bcnesacommons.Season.T_2021_2022)
    #generate_csv_for_season(bcnesacommons.Season.T_2020_2021)
    generate_csv_for_season(bcnesacommons.Season.T_2019_2020)
    #generate_csv_for_season(bcnesacommons.Season.T_2018_2019)

if __name__ == "__main__":
    main()


