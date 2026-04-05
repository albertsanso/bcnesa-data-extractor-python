from pathlib import Path
import importlib.util
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from common import bcnesacommons

PARSER_MODULE_PATH = Path(__file__).resolve().parent / "parse_played_matches_pdf_to_csv.py"
PARSER_SPEC = importlib.util.spec_from_file_location("played_matches_parse_played_matches_pdf_to_csv", PARSER_MODULE_PATH)
assert PARSER_SPEC is not None
PARSER_MODULE = importlib.util.module_from_spec(PARSER_SPEC)
assert PARSER_SPEC.loader is not None
PARSER_SPEC.loader.exec_module(PARSER_MODULE)

parse_pdf_to_rows = PARSER_MODULE.parse_pdf_to_rows
write_rows_to_csv = PARSER_MODULE.write_rows_to_csv

RESOURCES_DIR = ROOT_DIR / "resources"


def get_played_matches_pdf_path_for_season(season: bcnesacommons.Season) -> Path:
    return RESOURCES_DIR / "played-matches" / season.value / "played-matches.pdf"


def generate_csv_for_season(season: bcnesacommons.Season) -> Path | None:
    pdf_path = get_played_matches_pdf_path_for_season(season)
    if not pdf_path.exists():
        print(f"Skipping {season.value}: input PDF not found at {pdf_path}")
        return None

    rows, parsed_season, total_clubs, pages_processed = parse_pdf_to_rows(pdf_path)
    output_path = pdf_path.with_suffix(".csv")
    write_rows_to_csv(rows, output_path)

    print(f"Generated CSV for {season.value}: {output_path}")
    print(f"Season detected: {parsed_season or 'unknown'}")
    print(f"Total players found: {len(rows)}")
    print(f"Total clubs: {total_clubs}")
    print(f"Pages processed: {pages_processed}")

    return output_path


def generate_csvs_for_seasons(seasons: list[bcnesacommons.Season]) -> list[Path]:
    generated_files: list[Path] = []
    for season in seasons:
        output_path = generate_csv_for_season(season)
        if output_path is not None:
            generated_files.append(output_path)
    return generated_files


def main() -> None:
    seasons = [
        bcnesacommons.Season.T_2025_2026,
        bcnesacommons.Season.T_2024_2025,
        bcnesacommons.Season.T_2023_2024,
        bcnesacommons.Season.T_2022_2023,
        bcnesacommons.Season.T_2021_2022,
        bcnesacommons.Season.T_2020_2021,
        bcnesacommons.Season.T_2019_2020,
        bcnesacommons.Season.T_2018_2019,
    ]
    generate_csvs_for_seasons(seasons)


if __name__ == "__main__":
    main()


