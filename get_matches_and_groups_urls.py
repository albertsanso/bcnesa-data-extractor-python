import requests
from bs4 import BeautifulSoup
from selenium import webdriver

MAIN_RTBTT_URL = "https://www.rtbtt.com/"
MAIN_TABLE_SELECTOR_SINCE_2018 = "#main > div > table > tbody > tr > td > table:nth-child(1)"

def navigate_to_main_page():
    response = requests.get(MAIN_RTBTT_URL)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def extract_results_urls_and_years(soup):
    competicio_calendari_resultats_menu_selector = "#cssmenu > ul > li:nth-child(2) > ul > li:nth-child(1)"
    competicio_calendari_resultats_menu_element = soup.select_one(competicio_calendari_resultats_menu_selector)
    return extract_urls_and_years(competicio_calendari_resultats_menu_element)

def extract_jugadors_urls_and_years(soup):
    jugadors_menu_selector = "#cssmenu > ul > li:nth-child(2) > ul > li:nth-child(2)"
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

def navigate_results_for_year(the_year, years_urls_list):
    for year_url in years_urls_list:
        year = year_url[0]
        url = year_url[1]
        if the_year == year:
            driver = webdriver.Chrome()
            driver.get(url)

            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            #response = requests.get(url)
            #response.raise_for_status()
            #soup = BeautifulSoup(response.text, 'html.parser')
            return soup
    return None

def main():
    soup = navigate_to_main_page()
    results_urls_years = extract_results_urls_and_years(soup)
    #jugadors_urls_years = extract_jugadors_urls_and_years(soup)

    results_page = navigate_results_for_year('2024-2025', results_urls_years)
    #main_table_el = results_page.select(MAIN_TABLE_SELECTOR_SINCE_2018)
    main_table_el = results_page.find("div", id="main")

    print(main_table_el)

if __name__ == "__main__":
    main()