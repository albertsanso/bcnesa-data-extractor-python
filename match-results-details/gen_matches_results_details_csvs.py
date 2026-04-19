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

def gen_csv_for_season_competition_category(groups, season, competition, category, competition_match_days_count):
    input_folder = Path(bcnesacommons.RESOURCES_FOLDER) / "matches-results-details/pdf" / str(season) / str(competition) / category
    output_folder = Path(bcnesacommons.RESOURCES_FOLDER) / "matches-results-details/csv" / str(season) / str(competition) / category

    #input_folder = Path(bcnesacommons.RESOURCES_FOLDER) / "testing/matches-results-details/pdf" / str(season) / str(competition) / category
    #output_folder = Path(bcnesacommons.RESOURCES_FOLDER) / "testing/matches-results-details/csv" / str(season) / str(competition) / category

    for group in groups:
        generate_csv_from_pdfs_in_folder(input_folder, output_folder, group, competition_match_days_count, season)
        #break

def generate_csv_from_pdfs_in_folder(pdf_input_folder, csv_output_folder, group, competition_match_days_count, season):

    for jornada in range(1, competition_match_days_count+1):

        input_filename = "jornada{0}-g{1}.pdf".format(jornada, group["group"])
        input_full_path = pdf_input_folder / input_filename
        #print("I: " / input_full_path)

        output_filename = "jornada{0}-g{1}.csv".format(jornada, group["group"])
        output_full_path = csv_output_folder / output_filename
        #print("O: " / output_full_path)

        if os.path.exists(input_full_path):
            results_details = extract_matches_details(input_full_path, season, group["group"], jornada, competition_match_days_count)
            #print(results_details)

            plain_results = gen_plain_results(results_details)
            save_to_csv(plain_results, output_full_path)
            #break

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

def extract_matches_details(pdf_path, season, group, jornada, competition_match_days_count):
    #print(pdf_path)
    matches = []
    if os.path.exists(pdf_path):
        with pdfplumber.open(pdf_path) as pdf:

            try:
                for page in pdf.pages:
                    match_teams_info = {}
                    text = page.extract_text()
                    if not text:
                        continue

                    lines = text.split("\n")

                    match_info = {}

                    #if "2019-2020\\veterans\\2a\\jornada1-g2.pdf" in str(pdf_path):
                    #    pass

                    match_info["teams_info"] = fill_match_teams_info(get_match_teams_header_lines(lines, season))
                    match_info["match_info"] = fill_match_info(get_match_header_line(lines, season), group, jornada, competition_match_days_count, match_info["teams_info"])
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
                                    if "single_matches" not in match_info.keys():
                                        match_info["single_matches"] = []
                                    match_info["single_matches"].append(parsed_line["single_match_result"])
                                elif "match_score" in parsed_line.keys():
                                    match_info["match_score"] = parsed_line["match_score"]
                    matches.append(match_info)
            except Exception as e:
                print("FAILED PARSING: "+str(pdf_path))

    return matches

def gen_plain_results(matches):
    matchesListOfDicts = []
    try:
        for matchRow in matches:
            match_info = matchRow["match_info"]
            teams_info = matchRow["teams_info"]
            if match_info and "home_team" in match_info.keys():
                for single_match_row in matchRow["single_matches"]:
                    single_match_dict = {}
                    add_general_game_info_to_single_match(single_match_dict, match_info)
                    add_home_info_to_single_match(single_match_dict, single_match_row, match_info, teams_info)
                    add_away_info_to_single_match(single_match_dict, single_match_row, match_info, teams_info)
                    single_match_dict["game_type"] = "singles"
                    matchesListOfDicts.append(single_match_dict)

    except Exception as e:
        print(traceback.format_exc())

    return matchesListOfDicts

def add_general_game_info_to_single_match(single_match_dict, match_info):
    single_match_dict["jornada"] = match_info["jornada"]
    single_match_dict["match_date"] = match_info["date"]
    single_match_dict["venue"] = None
    single_match_dict["referee"] = None
    single_match_dict["game_type"] = None
    single_match_dict["set1"] = None
    single_match_dict["set2"] = None
    single_match_dict["set3"] = None
    single_match_dict["set4"] = None
    single_match_dict["set5"] = None
    return single_match_dict

def add_home_info_to_single_match(single_match_dict, single_match_row, match_info, teams_info):
    abc_team = list(filter(lambda x: x["letters"] == "ABC", teams_info))[0]["name"]
    xyz_team = list(filter(lambda x: x["letters"] == "XYZ", teams_info))[0]["name"]
    is_team_abc_home = abc_team == match_info["home_team"]

    if is_team_abc_home:
        side_match_info = single_match_row["player_abc"]
        home_team = abc_team
        home_player = single_match_row["player_abc"]
    else:
        side_match_info = single_match_row["player_xyz"]
        home_team = xyz_team
        home_player = single_match_row["player_xyz"]

    single_match_dict["home_team_id"] = None
    single_match_dict["home_team"] = home_team

    single_match_dict["home_position"] = home_player["letter"]
    single_match_dict["home_player_lic"] = home_player["license"]
    single_match_dict["home_player_name"] = home_player["name"]
    single_match_dict["game_result_home"] = home_player["score"]

    single_match_dict["home_player2_lic"] = None
    single_match_dict["home_player2_name"] = None
    single_match_dict["match_score_home"] = None
    single_match_dict["running_score_home"] = None

    return single_match_dict

def add_away_info_to_single_match(single_match_dict, single_match_row, match_info, teams_info):
    abc_team = list(filter(lambda x: x["letters"] == "ABC", teams_info))[0]["name"]
    xyz_team = list(filter(lambda x: x["letters"] == "XYZ", teams_info))[0]["name"]
    is_team_abc_home = abc_team == match_info["home_team"]

    if is_team_abc_home:
        side_match_info = single_match_row["player_xyz"]
        home_team = xyz_team
        home_player = single_match_row["player_xyz"]
    else:
        side_match_info = single_match_row["player_abc"]
        home_team = abc_team
        home_player = single_match_row["player_abc"]


    single_match_dict["away_team_id"] = None
    single_match_dict["away_team"] = home_team

    single_match_dict["away_position"] = home_player["letter"]
    single_match_dict["away_player_lic"] = home_player["license"]
    single_match_dict["away_player_name"] = home_player["name"]
    single_match_dict["game_result_away"] = home_player["score"]

    single_match_dict["away_player2_lic"] = None
    single_match_dict["away_player2_name"] = None
    single_match_dict["match_score_away"] = None
    single_match_dict["running_score_away"] = None

    return single_match_dict

def get_match_teams_header_lines(all_lines, season):
    if season == bcnesacommons.Season.T_2019_2020.value:
        return all_lines[:5]
    else:
        return all_lines[:6]

def get_match_header_line(all_lines, season):
    if season == bcnesacommons.Season.T_2019_2020.value:
        return all_lines[3]
    else:
        return all_lines[4]

def get_body_lines(all_lines, season):
    return all_lines[6:]

def fill_match_teams_info(lines):
    match_acta_teams = lines[-1]  # ABC CTT CASTELLGALÍ XYZ CTT LA POBLA DE LILLET

    teams_pattern_string = r'(ABC|XYZ+)\s+(.*?)\s+(ABC|XYZ+)\s+(.*)'
    teams_matches_pattern = re.compile(teams_pattern_string)
    teams_match = teams_matches_pattern.search(match_acta_teams)
    a,b,c,d = teams_match.groups()
    if teams_match:
        return  [
                {"letters": a, "name": b},
                {"letters": c, "name": d} ]
    else:
        return []

def fill_match_info(line, group, jornada, competition_match_days_count, teams):
    match_info = line

    abc_team = list(filter(lambda x: x["letters"] == "ABC", teams))[0]["name"]
    xyz_team = list(filter(lambda x: x["letters"] == "XYZ", teams))[0]["name"]

    home_team, away_team = determine_home_away(line, abc_team, xyz_team)

    pattern = r'Acta\s+\d+\s+(\d{2}/\d{2}/\d{2,4})\s+'
    match = re.match(pattern, match_info)
    if match:
        date = match.group(1)  # 01/10/24
        return {
            "date": date,
            "home_team": home_team,
            "away_team": away_team,
            "group": group,
            "jornada": jornada,
            "competition_match_days_count": competition_match_days_count
        }
    return {}


def determine_home_away(text, teamabc, teamxyz):
    """
    Determines which team is home and which is away based on their position in text.
    Uses partial matching - teams don't need to appear exactly as in text.

    Returns (home_team, away_team) using the original team name strings,
    or (None, None) if either team can't be found.
    """
    def get_significant_chunks(name, min_len=4):
        words = name.split()
        chunks = []
        for i in range(len(words)):
            for j in range(i+1, len(words)+1):
                chunk = ' '.join(words[i:j])
                if len(chunk) >= min_len:
                    chunks.append(chunk)
        return sorted(chunks, key=len, reverse=True)

    def find_first_position(text, team_name):
        chunks = get_significant_chunks(team_name)
        for chunk in chunks:
            m = re.search(re.escape(chunk), text, re.IGNORECASE)
            if m:
                return m.start()
        return None

    header_match = re.match(r'Acta\s+\d+\s+\d{2}/\d{2}/\d{2,4}\s+(.*)', text)
    if not header_match:
        return None, None

    match_body = header_match.group(1)
    pos_abc = find_first_position(match_body, teamabc)
    pos_xyz = find_first_position(match_body, teamxyz)

    if pos_abc is None or pos_xyz is None:
        return None, None

    return (teamabc, teamxyz) if pos_abc < pos_xyz else (teamxyz, teamabc)

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
            "player_abc": {
                "letter": letter_player_1,
                "license": license_player_1,
                "name": name_player_1,
                "score": score_player_1
            },
            "player_xyz": {
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
    generate_csv_for_season(bcnesacommons.Season.T_2025_2026)
    #generate_csv_for_season(bcnesacommons.Season.T_2024_2025)
    #generate_csv_for_season(bcnesacommons.Season.T_2023_2024)
    #generate_csv_for_season(bcnesacommons.Season.T_2022_2023)
    #generate_csv_for_season(bcnesacommons.Season.T_2021_2022)
    #generate_csv_for_season(bcnesacommons.Season.T_2020_2021)
    #generate_csv_for_season(bcnesacommons.Season.T_2019_2020)
    #generate_csv_for_season(bcnesacommons.Season.T_2018_2019)

if __name__ == "__main__":
    main()


