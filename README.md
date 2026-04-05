# bcnesa-data-extractor-python

## Parse "Encontres disputats per jugador/a" PDF to CSV

Main script: `played-matches/parse_played_matches_pdf_to_csv.py`

Compatibility wrapper: `parse_played_matches_pdf_to_csv.py`

Runner by season: `played-matches/gen_played_matches_csvs.py`

### Run

```bash
python "played-matches/parse_played_matches_pdf_to_csv.py" "resources/played-matches/pdf/2024-2025/played-matches.pdf"
```

The script writes the CSV next to the input PDF (same name, `.csv` extension) and prints:
- total players found
- total clubs
- pages processed

### Run by season

```bash
python "played-matches/gen_played_matches_csvs.py"
```

Edit the `seasons` list inside `played-matches/gen_played_matches_csvs.py` to enable more seasons.

### Basic tests

```bash
python -m unittest tests/test_parse_played_matches_pdf_to_csv.py
python -m unittest tests/test_gen_played_matches_csvs.py
```

