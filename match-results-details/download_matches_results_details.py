import requests
from pathlib import Path
from bs4 import BeautifulSoup
from common import bcnesacommons

import urllib.request
import traceback

MAIN_RTBTT_URL = "https://www.rtbtt.com/"

CATEGORY_MAPPING = {
    "PREF_G1": { "folder": "preferent/1", "group": "1"},
    "PREF_G2": { "folder": "preferent/1", "group": "2"},
    "PREF_G3": { "folder": "preferent/1", "group": "3"},
    "PRIMERA_G1": { "folder": "senior/1", "group": "1"},
    "PRIMERA_G2": { "folder": "senior/1", "group": "2"},
    "PRIMERA_G3": { "folder": "senior/1", "group": "3"},
    "SEGONA_A_G1": { "folder": "senior/2a", "group": "1"},
    "SEGONA_A_G2": { "folder": "senior/2a", "group": "2"},
    "SEGONA_A_G3": { "folder": "senior/2a", "group": "3"},
    "SEGONA_B_G1": { "folder": "senior/2b", "group": "1"},
    "SEGONA_B_G2": { "folder": "senior/2b", "group": "2"},
    "SEGONA_B_G3": { "folder": "senior/2b", "group": "3"},
    "TERCERA_G1": { "folder": "senior/3", "group": "1"},
    "TERCERA_G2": { "folder": "senior/3", "group": "2"},
    "TERCERA_G3": { "folder": "senior/3", "group": "3"},
    "TERCERA_G4": { "folder": "senior/3", "group": "4"},
    "TERCERA_G5": { "folder": "senior/3", "group": "5"},
    "TERCERA_A_G1": { "folder": "senior/3a", "group": "1"},
    "TERCERA_A_G2": { "folder": "senior/3a", "group": "2"},
    "TERCERA_A_G3": { "folder": "senior/3a", "group": "3"},
    "TERCERA_B_G1": { "folder": "senior/3b", "group": "1"},
    "TERCERA_B_G2": { "folder": "senior/3b", "group": "2"},
    "TERCERA_B_G3": { "folder": "senior/3b", "group": "3"},
    "TERCERA_B_G4": { "folder": "senior/3b", "group": "4"},
    "TERCERA_B_G5": { "folder": "senior/3b", "group": "5"},
    "TERCERA_B_G6": { "folder": "senior/3b", "group": "6"},
    "QUARTA_G1": { "folder": "senior/4", "group": "1"},
    "QUARTA_G2": { "folder": "senior/4", "group": "2"},
    "QUARTA_G3": { "folder": "senior/4", "group": "3"},
    "QUARTA_G4": { "folder": "senior/4", "group": "4"},
    "QUARTA_G5": { "folder": "senior/4", "group": "5"},
    "VET_1_G1": { "folder": "veterans/1", "group": "1"},
    "VET_1_G2": { "folder": "veterans/1", "group": "2"},
    "VET_1_G3": { "folder": "veterans/1", "group": "3"},
    "VET_2_A_G1": { "folder": "veterans/2a", "group": "1"},
    "VET_2_A_G2": { "folder": "veterans/2a", "group": "2"},
    "VET_2_B_G1": { "folder": "veterans/2b", "group": "1"},
    "VET_2_B_G2": { "folder": "veterans/2b", "group": "2"},
    "VET_3_A_G1": { "folder": "veterans/3a", "group": "1"},
    "VET_3_A_G2": { "folder": "veterans/3a", "group": "2"},
    "VET_3_B_G1": { "folder": "veterans/3b", "group": "1"},
    "VET_3_B_G2": { "folder": "veterans/3b", "group": "2"},
    "VET_3_B_G3": { "folder": "veterans/3b", "group": "3"},
    "VET_3_B_G4": { "folder": "veterans/3b", "group": "4"},
    "VET_3_C_G1": { "folder": "veterans/3c", "group": "1"},
    "VET_3_C_G2": { "folder": "veterans/3c", "group": "2"},
    "VET_3_C_G3": { "folder": "veterans/3c", "group": "3"},
    "VET_3_C_G4": { "folder": "veterans/3c", "group": "4"},
    "VET_3_C_G5": { "folder": "veterans/3c", "group": "5"},
    "VET_4_A_G1": { "folder": "veterans/4a", "group": "1"},
    "VET_4_A_G2": { "folder": "veterans/4a", "group": "2"},
    "VET_4_B_G1": { "folder": "veterans/4b", "group": "1"},
    "VET_4_B_G2": { "folder": "veterans/4b", "group": "2"}
}

def extract_actes_urls_and_years(soup):
    jugadors_menu_selector = "#cssmenu > ul > li:nth-child(2) > ul > li:nth-child(3)"
    jugadors_menu_element = soup.select_one(jugadors_menu_selector)
    return extract_urls_and_years(jugadors_menu_element)

def extract_urls_and_years(element):
    anys_item_elements = element.find_all("li")

    urls_years = []
    for that_year_item_element in anys_item_elements:
        js_href = that_year_item_element.find("a").get("href")
        that_year = that_year_item_element.get_text()
        results_for_that_year_url = js_href.strip("javascript:loadurl('").rstrip("','main');")
        urls_years.append((that_year, results_for_that_year_url))
    return urls_years

def navigate_to_main_page():
    response = requests.get(MAIN_RTBTT_URL)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def get_urls_to_actes_page(url, year):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    div_elements = soup.find_all('div', class_=['Estilo54', 'Estilo158', 'Estilo160'])
    filtered_div_elements = [td for td in div_elements if all(cls in td.get('class', []) for cls in ['Estilo54', 'Estilo158', 'Estilo160'])]

    actes_pages_url = []
    for filtered_div_element in filtered_div_elements:

        actas_a_elements = filtered_div_element.find_all("a")
        for acta_a_element in actas_a_elements:
            js_url = acta_a_element.get("href")
            acta_url = extract_acta_url_from_href(js_url)
            actes_pages_url.append(acta_url)

    return actes_pages_url

def extract_acta_url_from_href(js_url):
    if js_url.startswith("javascript:loadurl"):
        part1 = js_url.removeprefix("javascript:loadurl('")
        part2 = part1.removesuffix("','main');")
        if part2.startswith("https://www.rtbtt.com/actes"):
            return part2.replace('\n', '')
    return None

def filter_by_year(results_urls_years, the_year):
    return [t for t in results_urls_years if t[0] == the_year]

def filter_by_years_list(results_urls_years, the_years_list):
    return [t for t in results_urls_years if t[0] in the_years_list]

def exclude_years_list(results_urls_years, the_year):
    return [t for t in results_urls_years if t[0] not in the_year]

def get_all_pdfs_urls(the_years_list=None):
    soup = navigate_to_main_page()
    original_results_urls_years = extract_actes_urls_and_years(soup)

    results_urls_years = exclude_years_list(original_results_urls_years, ["2025-2026"])

    if the_years_list is not None:
        results_urls_years = filter_by_years_list(results_urls_years, the_years_list)

    pdfs = []
    for url_info in results_urls_years:
        year = url_info[0]
        url = url_info[1]
        actes_pages_url = get_urls_to_actes_page(url, year)
        for url in actes_pages_url:
            if url is not None:
                pdf_url = get_urls_to_pdfs(url)
                pdfs.extend(pdf_url)
    return pdfs

def navigate_to_acta_page_from_url(acta_page_url):
    response = requests.get(acta_page_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def get_urls_to_pdfs(acta_page_url):
    soup = navigate_to_acta_page_from_url(acta_page_url)
    a_elements = soup.find_all("a")
    visited = set()
    pdf_urls=[]
    for a_el in a_elements:
        href_el = a_el.get("href")
        if href_el not in visited:
            visited.add(href_el)
            url = mount_pdf_url(acta_page_url, href_el)
            pdf_urls.append(url)
    return pdf_urls

def mount_pdf_url(base_url, pdf_url):
    new_base_url = "/".join(base_url.split("/")[:-1])
    pdf_file = pdf_url.split("/")[-1]
    new_url = new_base_url+"/"+pdf_file
    return new_url

def download_for_season(season):
    pdfs_urls = get_all_pdfs_urls(season.value)
    for pdf_url in pdfs_urls:
        download_for_pdf_url(pdf_url, season)

def download_for_pdf_url(pdf_url, season):
    url_parts = pdf_url.split("/")
    filename = url_parts[-1]
    category_path = url_parts[-2]

    if category_path not in CATEGORY_MAPPING.keys():
        print("category: "+category_path+" Not considered.")
    else:
        category_info_mapped = CATEGORY_MAPPING[category_path]
        mapped_group = category_info_mapped["group"]
        folder = Path(bcnesacommons.RESOURCES_FOLDER) / "matches-results-details/pdf" / str(season.value) / str(category_info_mapped["folder"])
        filename = filename.split(".")[0]+"-g"+mapped_group+"."+filename.split(".")[1]
        try:
            file_path = Path(folder) / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            #print(f"Downloading: {pdf_url}")
            urllib.request.urlretrieve(pdf_url, file_path)

        except Exception as e:
            print(f"Error downloading {pdf_url} to {file_path}")
            print(traceback.format_exc())


if __name__ == "__main__":
    pass
    #download_for_season(bcnesacommons.Season.T_2024_2025)
    #download_for_season(bcnesacommons.Season.T_2023_2024)
    #download_for_season(bcnesacommons.Season.T_2022_2023)
    #download_for_season(bcnesacommons.Season.T_2021_2022)
    #download_for_season(bcnesacommons.Season.T_2020_2021)
    download_for_season(bcnesacommons.Season.T_2019_2020)
    #download_for_season(bcnesacommons.Season.T_2018_2019)

