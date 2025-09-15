import requests
import pdfplumber
import re
from datetime import datetime
import tempfile

PDF_PATH = "QUA_G3.pdf"

def clean_whitespace(s):
    return " ".join(s.split())

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

def download_pdf(url):
    """Download the PDF and return a temporary file path."""
    response = requests.get(url)
    response.raise_for_status()
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp.write(response.content)
    temp.close()
    return temp.name

def main():
    PDF_URL = "https://www.rtbtt.com/lligues2425/QUA_G3.pdf"
    pdf_path = download_pdf(PDF_URL)
    matches = extract_matches(pdf_path)
    for m in matches:
        print(f"{m['date'].strftime('%Y-%m-%d %H:%M')} : {m['home']} vs {m['away']} -> {m['home_score']}-{m['away_score']} (Match ID {m['match_id']})")

if __name__ == "__main__":
    main()
