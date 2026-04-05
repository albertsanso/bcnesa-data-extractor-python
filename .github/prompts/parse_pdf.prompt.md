---
mode: 'agent'
description: 'Parse RTBTT player matches PDF to CSV'
tools: ['terminal']
---

Generate a Python script that parses the RTBTT "Encontres disputats per jugador/a" PDF located at `${input:pdfPath:Full path to the PDF file}` and outputs a CSV file...

Here's a detailed plan/prompt you can use to generate the Python script:

---

## Prompt / Plan: PDF → CSV Parser for RTBTT Player Matches

**Goal:** Parse an RTBTT "Encontres disputats per jugador/a" PDF and output a single CSV with one row per player, all match columns, plus `Club` and `Season` as additional columns.

---

### Context to provide to the code-generating AI:

> **Input:** A PDF file path (e.g. `encontres_disputats_per_jugador-2025-2026.pdf`)
> **Output:** A single CSV file with one row per player and the following columns:
>
> `Club, Season, NomJugador, Núm, Edat, Llic, Total, SUM, SUF, DHM, DHF, PDM, PDF, SDM, TDM, Sen_Pref, Sen_1a, Sen_2aA, Sen_2aB, Sen_3aA, Sen_3aB, Sen_4a, Vet_1a, Vet_2aA, Vet_2aB, Vet_3aA, Vet_3aB, Vet_4aA, Vet_4aB`

---

### Key parsing facts (critical for the script to work):

1. **Tool to use:** `pdfplumber` — use `page.extract_text()` with layout mode, or better `pdfplumber` with `layout=True` to preserve column spacing.

2. **Season extraction:** Parse from the filename. Pattern: `YYYY-YYYY` anywhere in the filename (e.g. `encontres_disputats_per_jugador-2025-2026.pdf` → `2025-2026`). If not found in filename, use the date printed at the bottom of pages (e.g. `01/04/2026`).

3. **Club name detection:** Each page starts with a line like:
   ```
   Club    ASSOCIACIÓ VEÏNAL DELS MOLINS (304 TT)
   ```
   The club name persists across multiple consecutive pages until a new `Club` line appears. Strip the `Club` prefix and trim whitespace.

4. **Header line detection:** Skip lines that match the two-line header pattern starting with `NomJugador/a` and the category subheader line (`Pref.`, `1a`, `2aA`, etc.).

5. **Player line format** (space-delimited, positional):
   - Player name: first token(s) — all caps, may be multi-word (e.g. `ACEDO Francisco Jose`, `GARCIA DE SORIA Albert`)
   - Player number: integer (4–5 digits)
   - Age category: token like `SEN`, `V+50`, `V+65`, `CAD-1`, `JUV-2`, `INF-2`, `BEN-2`, `ALE-1`, `S21-1`
   - Licence: token matching pattern like `C-SEM`, `A2-VEM`, `B-BEM`, etc. — **may wrap to the next line** (e.g. `A2-` on one line, `CAM` on the next)
   - Numeric columns: up to 22 integer values (many blank/zero), positionally aligned

6. **Line wrapping:** Some player entries span 2 lines because the licence code wraps. Detect continuation lines: a line that starts with whitespace and contains only a licence suffix (e.g. `CAM`, `VEM`, `INF`) with no player number. Merge these into the previous player line before parsing.

7. **Footer lines:** Skip lines matching the date+page pattern: `DD/MM/YYYY` and `Pàgina N de 142`.

8. **Numeric columns:** After the licence field, there are up to 22 positional numeric columns. Many will be empty (treat as `0`). Extract by splitting on 2+ spaces after the licence field, or use fixed character offsets derived from the header line positions.

9. **Column position strategy (recommended):** On each page, detect the header line and record the character offset of each column name. Use those offsets ±3 chars to slice each player line into fields. This is more robust than pure token splitting given variable name lengths.

---

### Script requirements:

- Accept the PDF path as a **command-line argument** (`sys.argv[1]`)
- Output CSV to the same directory as the input, named `<original_name>.csv`
- Use `pdfplumber` (install: `pip install pdfplumber`)
- Empty numeric cells → `0`
- Print a summary at the end: total players found, total clubs, pages processed
- Handle encoding gracefully (the PDF contains accented characters like `à`, `é`, `ó`)

---

### Validation checklist for the generated script:

- [ ] Club name correctly resets per section (not per page — a club can span multiple pages)
- [ ] Wrapped licence lines are merged before parsing
- [ ] Player names with 3 words (e.g. `GARCIA DE SORIA Albert`) are captured fully
- [ ] All 22 numeric columns are present in every row (zeros where blank)
- [ ] Season column is populated for every row
- [ ] No header rows appear in the CSV output
- [ ] Footer/date lines are excluded

---

You can paste this plan directly into a new chat with Claude (or any code-generating AI) and it will have everything needed to produce a working script. The key tricky parts are explicitly called out: line wrapping, multi-word names, club persistence across pages, and positional column parsing.