import csv
import re
import sys
from datetime import datetime
from pathlib import Path

import pdfplumber

CSV_COLUMNS = [
    "Club",
    "Season",
    "NomJugador",
    "Núm",
    "Edat",
    "Llic",
    "Total",
    "SUM",
    "SUF",
    "DHM",
    "DHF",
    "PDM",
    "PDF",
    "SDM",
    "TDM",
    "Sen_Pref",
    "Sen_1a",
    "Sen_2aA",
    "Sen_2aB",
    "Sen_3aA",
    "Sen_3aB",
    "Sen_4a",
    "Vet_1a",
    "Vet_2aA",
    "Vet_2aB",
    "Vet_3aA",
    "Vet_3aB",
    "Vet_4aA",
    "Vet_4aB",
]

NUMERIC_COLUMNS = CSV_COLUMNS[6:]

HEADER_TOKENS = [
    "Total",
    "SUM",
    "SUF",
    "DHM",
    "DHF",
    "PDM",
    "PDF",
    "SDM",
    "TDM",
    "Sen.",
    "Sen.",
    "Sen.",
    "Sen.",
    "Sen.",
    "Sen.",
    "Sen.",
    "Vet.",
    "Vet.",
    "Vet.",
    "Vet.",
    "Vet.",
    "Vet.",
    "Vet.",
]

CLUB_RE = re.compile(r"^\s*Club\s+(.+?)\s*$")
SEASON_RE = re.compile(r"(20\d{2}-20\d{2})")
FOOTER_RE = re.compile(r"^\s*(\d{2}/\d{2}/\d{4}).*P\S*gina\s+\d+\s+de\s+\d+\s*$", re.IGNORECASE)
CONTINUATION_RE = re.compile(r"^\s+[A-Z0-9]{2,6}\s*$")
INCOMPLETE_LIC_RE = re.compile(r"(\b[A-Z0-9]{1,3}-)\s+(\d+)")
PLAYER_PREFIX_RE = re.compile(
    r"^\s*(?P<name>.+?)\s+(?P<num>\d{3,5})\s+(?P<age>[A-Z0-9+\-]+)\s+(?P<lic>[A-Z0-9]{1,3}-[A-Z0-9]+)\s+"
)

# Fixed numeric column tokens mapped to their index in NUMERIC_COLUMNS / CSV_COLUMNS
# (lookup by name handles seasons where columns are absent or in different order)
_FIXED_NAMED_TOKENS: list[tuple[str, int]] = [
    ("Total", 0),
    ("SUM",   1),
    ("SUF",   2),
    ("DHM",   3),
    ("DHF",   4),
    ("PDM",   5),
    ("PDF",   6),
    ("SDM",   7),
    ("TDM",   8),
]
# Max Sen./Vet. columns per season (2024-2025 = 7+7; older seasons = 5–6 each)
_MAX_SEN_COLS = 7
_MAX_VET_COLS = 7


def extract_season_from_filename(pdf_path: Path) -> str | None:
    # Check the filename first (e.g. found-matches-2024-2025.pdf)
    match = SEASON_RE.search(pdf_path.name)
    if match:
        return match.group(1)
    # Fall back to parent directory names (e.g. .../2022-2023/played-matches.pdf)
    for parent in pdf_path.parents:
        match = SEASON_RE.search(parent.name)
        if match:
            return match.group(1)
    return None


def season_from_footer_date(date_text: str) -> str:
    date_obj = datetime.strptime(date_text, "%d/%m/%Y")
    if date_obj.month >= 8:
        return f"{date_obj.year}-{date_obj.year + 1}"
    return f"{date_obj.year - 1}-{date_obj.year}"


def extract_column_starts(lines: list[str], fallback: list[int] | None) -> list[int] | None:
    # Accept both "NomJugador/a" (2023-2024+) and "NomJugador" (2022-2023 and older)
    header_line = next((line for line in lines if "NomJugador" in line and "Total" in line), None)
    if not header_line:
        return fallback

    # "Total" marks the start of the numeric-columns area in every season
    total_pos = header_line.find("Total")
    if total_pos < 0:
        return fallback
    numeric_area = header_line[total_pos:]  # Slice from "Total" onwards

    # Named lookup for the 9 fixed columns.
    # Absent columns (e.g. SUM/PDF in 2018-2019) get sentinel -1 → value 0 in output.
    # Different column order (e.g. DHF before DHM in 2018-2019) is handled naturally.
    fixed_starts: list[int] = [-1] * 9
    for token, col_idx in _FIXED_NAMED_TOKENS:
        pos = numeric_area.find(token)
        if pos >= 0:
            fixed_starts[col_idx] = total_pos + pos

    # Locate Sen. columns dynamically (5–7 depending on season)
    search_from = total_pos
    sen_starts: list[int] = []
    while len(sen_starts) < _MAX_SEN_COLS:
        token_idx = header_line.find("Sen.", search_from)
        if token_idx < 0:
            break
        sen_starts.append(token_idx)
        search_from = token_idx + len("Sen.")

    # Locate Vet. columns dynamically (5–7 depending on season)
    vet_starts: list[int] = []
    while len(vet_starts) < _MAX_VET_COLS:
        token_idx = header_line.find("Vet.", search_from)
        if token_idx < 0:
            break
        vet_starts.append(token_idx)
        search_from = token_idx + len("Vet.")

    if not sen_starts and not vet_starts:
        return fallback

    # Pad missing Sen./Vet. slots with -1 sentinel (→ value 0 in output)
    padded_sen = sen_starts + [-1] * (_MAX_SEN_COLS - len(sen_starts))
    padded_vet = vet_starts + [-1] * (_MAX_VET_COLS - len(vet_starts))

    result = fixed_starts + padded_sen + padded_vet
    if len(result) != len(NUMERIC_COLUMNS):
        return fallback

    return result


def is_header_or_noise(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    # Title line (both "jugador/a" and "jugador" variants)
    if "Encontres disputats per jugador" in stripped:
        return True
    # Column header line (both "NomJugador/a" and "NomJugador" variants)
    if "NomJugador" in stripped and "Total" in stripped:
        return True
    # Sub-header categories line (always starts with "Pref." after stripping)
    if stripped.startswith("Pref."):
        return True
    return False


def merge_wrapped_licence_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    for line in lines:
        if merged and CONTINUATION_RE.match(line):
            suffix = line.strip()
            last_line = merged[-1]
            patched_line = INCOMPLETE_LIC_RE.sub(rf"\1{suffix} \2", last_line, count=1)
            if patched_line != last_line:
                merged[-1] = patched_line
                continue
        merged.append(line)
    return merged


def parse_numeric_values(line: str, starts: list[int]) -> list[int]:
    values: list[int] = []
    for idx, start in enumerate(starts):
        if start == -1:
            # Sentinel: column not present in this season's PDF layout
            values.append(0)
            continue
        # Find the next non-sentinel start to determine the column boundary
        end = len(line)
        for j in range(idx + 1, len(starts)):
            if starts[j] != -1:
                end = starts[j]
                break
        segment = line[start:end] if start < len(line) else ""
        number_match = re.search(r"\d+", segment)
        values.append(int(number_match.group(0)) if number_match else 0)
    return values


def parse_player_line(line: str, starts: list[int]) -> dict[str, str | int] | None:
    if not starts:
        return None

    prefix_match = PLAYER_PREFIX_RE.match(line)
    if not prefix_match:
        return None

    parsed = {
        "NomJugador": " ".join(prefix_match.group("name").split()),
        "Núm": prefix_match.group("num"),
        "Edat": prefix_match.group("age"),
        "Llic": prefix_match.group("lic"),
    }

    numeric_values = parse_numeric_values(line, starts)
    for col, value in zip(NUMERIC_COLUMNS, numeric_values, strict=True):
        parsed[col] = value

    return parsed


def parse_pdf_to_rows(pdf_path: Path) -> tuple[list[dict[str, str | int]], str, int, int]:
    rows: list[dict[str, str | int]] = []
    clubs_seen: set[str] = set()
    current_club: str = ""
    pages_processed = 0
    footer_date = None
    column_starts: list[int] | None = None

    season = extract_season_from_filename(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(layout=True)
            if not page_text:
                continue

            pages_processed += 1
            page_lines = [line.rstrip("\n") for line in page_text.splitlines() if line.strip()]
            column_starts = extract_column_starts(page_lines, column_starts)

            filtered_lines: list[str] = []
            for line in page_lines:
                club_match = CLUB_RE.match(line)
                if club_match:
                    current_club = club_match.group(1).strip()
                    if current_club:
                        clubs_seen.add(current_club)
                    continue

                footer_match = FOOTER_RE.match(line)
                if footer_match:
                    if footer_date is None:
                        footer_date = footer_match.group(1)
                    continue

                if is_header_or_noise(line):
                    continue

                filtered_lines.append(line)

            for line in merge_wrapped_licence_lines(filtered_lines):
                if not column_starts:
                    continue

                parsed_line = parse_player_line(line, column_starts)
                if not parsed_line:
                    continue

                row = {
                    "Club": current_club,
                    "Season": "",
                }
                row.update(parsed_line)
                rows.append(row)

    if not season and footer_date:
        season = season_from_footer_date(footer_date)

    if not season:
        season = ""

    for row in rows:
        row["Season"] = season

    return rows, season, len(clubs_seen), pages_processed


def write_rows_to_csv(rows: list[dict[str, str | int]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python parse_played_matches_pdf_to_csv.py <path_to_pdf>")
        return 1

    pdf_path = Path(sys.argv[1]).expanduser().resolve()
    if not pdf_path.exists():
        print(f"Input PDF not found: {pdf_path}")
        return 1

    if pdf_path.suffix.lower() != ".pdf":
        print(f"Input file is not a PDF: {pdf_path}")
        return 1

    rows, season, total_clubs, pages_processed = parse_pdf_to_rows(pdf_path)
    output_path = pdf_path.with_suffix(".csv")
    write_rows_to_csv(rows, output_path)

    print(f"Output CSV: {output_path}")
    print(f"Season: {season or 'unknown'}")
    print(f"Total players found: {len(rows)}")
    print(f"Total clubs: {total_clubs}")
    print(f"Pages processed: {pages_processed}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


