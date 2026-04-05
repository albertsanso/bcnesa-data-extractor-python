import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent / "played-matches" / "parse_played_matches_pdf_to_csv.py"
SPEC = importlib.util.spec_from_file_location("played_matches_parse_played_matches_pdf_to_csv", MODULE_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

CSV_COLUMNS = MODULE.CSV_COLUMNS
NUMERIC_COLUMNS = MODULE.NUMERIC_COLUMNS
HEADER_TOKENS = MODULE.HEADER_TOKENS
extract_season_from_filename = MODULE.extract_season_from_filename
season_from_footer_date = MODULE.season_from_footer_date
extract_column_starts = MODULE.extract_column_starts
is_header_or_noise = MODULE.is_header_or_noise
merge_wrapped_licence_lines = MODULE.merge_wrapped_licence_lines
parse_numeric_values = MODULE.parse_numeric_values
parse_player_line = MODULE.parse_player_line
parse_pdf_to_rows = MODULE.parse_pdf_to_rows
write_rows_to_csv = MODULE.write_rows_to_csv
main = MODULE.main


if __name__ == "__main__":
    raise SystemExit(main())
