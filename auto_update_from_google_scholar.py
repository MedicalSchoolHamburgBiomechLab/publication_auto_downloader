import math
import re
from difflib import SequenceMatcher
from time import sleep

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By


# from utils.convenience import save_dataframe


def clean_latex_string(s):
    if pd.isna(s):
        return s
    latex_to_unicode = {
        r'\\"a': 'ä',
        r'\\"o': 'ö',
        r'\\"u': 'ü',
        r"\\'e": 'é',
        r"\\ss": 'ß',
        r"\\c{c}": 'c',
        # Add more replacements as needed
    }

    for latex, unicode in latex_to_unicode.items():
        s = re.sub(r"{" + latex + "}", unicode, s)
    # Replace LaTeX accent commands with plain text accents
    s = re.sub(r"{\\+'+\\([a-zA-Z])}", r"\1", s)
    s = re.sub(r"{\\+\^+\\([a-zA-Z])}", r"\1", s)
    s = re.sub(r"{\\+'([a-zA-Z])}", r"\1", s)
    s = re.sub(r"{\\+`([a-zA-Z])}", r"\1", s)
    s = re.sub(r'{\\+"([a-zA-Z])}', r'\1', s)
    s = re.sub(r'{\\+~([a-zA-Z])}', r'\1', s)
    s = re.sub(r'{\\+c([a-zA-Z])}', r'\1', s)
    # Replace LaTeX ampersand
    s = s.replace(r'\&', '&')

    # Remove any remaining LaTeX commands
    s = re.sub(r"\\+[a-zA-Z]+\{", "", s)
    s = s.replace("}", "")

    return s


def get_institute_authors():
    url_scholar = "https://scholar.google.de/citations?hl=en&user=lLjLunUAAAAJ&view_op=list_works&authuser=2&gmla=AJsN-F5_sl8556qmuNJRGl18SjowYoLY2ki22Bh8kBZlb9FrmatzjMU2LFwQcdtFka3OuzGLatsQyRkN4azMzyDYf3JzxyeRzEwYQq_mYQyYT1x_lpC1WHE"
    browser = webdriver.Chrome()
    browser.get(url_scholar)
    co_authors_div = browser.find_element(By.XPATH, '/html/body/div/div[12]/div[2]/div/div[1]/div[2]/ul')
    author_anchors = co_authors_div.find_elements(By.XPATH, './li/div/span[2]/a')
    publications = list()
    for author_el in author_anchors:
        author = author_el.text
        print(author)
        author_el.click()
        sleep(1)
        # find "YEAR" button nand sort by year
        year_btn = browser.find_element(By.XPATH, '//*[@id="gsc_a_ha"]/a')
        year_btn.click()
        sleep(1)
        table_div = browser.find_element(By.XPATH, "//*[@id='gsc_a_tw']")
        elements = table_div.find_elements(By.XPATH, "./table/tbody/tr")
        for el in elements:
            year = el.text[-4:]
            if year != '2024':
                continue
            if year == '2023':
                break
            print(year)
            title = el.find_element(By.XPATH, "./td/a").text
            resp = get(f"https://api.crossref.org/works?query.bibliographic={title}")
            crossref_results = resp.json().get('message', dict()).get('items', list())
            crossref_result = get_best_match({'title': title, 'source': None}, crossref_results)
            if not crossref_result:
                print(f'WARNING: No match found for title: {title}')
                continue
            publication = get_cleaned_dict(crossref_result)
            publications.append(publication)
        browser.back()
        browser.back()
        sleep(2)
    foo = 1
    df = pd.DataFrame(publications)
    # make author list to string
    df['author'] = df['author'].apply('; '.join)
    df['year'] = df['year'].apply(lambda x: int(x) if not math.isnan(x) else '')
    df = df.applymap(lambda x: '' if x == [''] else x)
    # remove duplicates based on URL
    df = df.drop_duplicates(subset='URL')
    df.to_excel('iies_publications.xlsx', index=False)


def get_pub_titles():
    url_scholar = "https://scholar.google.de/citations?hl=en&user=lLjLunUAAAAJ&view_op=list_works&authuser=2&gmla=AJsN-F5_sl8556qmuNJRGl18SjowYoLY2ki22Bh8kBZlb9FrmatzjMU2LFwQcdtFka3OuzGLatsQyRkN4azMzyDYf3JzxyeRzEwYQq_mYQyYT1x_lpC1WHE"
    browser = webdriver.Chrome()
    browser.get(url_scholar)
    # Expand the page
    show_more_btn = browser.find_element(By.XPATH, '//*[@id="gsc_bpf_more"]/span/span[2]')
    show_more_btn.click()
    # needs some time to re-fetch the extended page
    sleep(2)

    # titles = browser.find_elements(By.XPATH,"//*[@id='gsc_a_b']/tr[2]/td[1]/a")
    table_div = browser.find_element(By.XPATH, "//*[@id='gsc_a_tw']")
    elements = table_div.find_elements(By.XPATH, "./table/tbody/tr")
    entries = list()
    for el in elements:
        entry = dict()
        title = el.find_element(By.XPATH, "./td/a").text
        authors = el.find_element(By.XPATH, "./td/div[1]").text
        source = el.find_element(By.XPATH, "./td/div[2]").text
        year = el.find_element(By.XPATH, "./td[3]").text
        entry['title'] = title
        entry['authors'] = authors
        entry['source'] = source
        entry['year'] = year
        entries.append(entry)
    browser.close()
    return entries


def get_cite_btn(brwsr):
    cite = brwsr.find_elements(By.TAG_NAME, 'span')
    out = None
    for c in cite:
        if c.text.lower() == 'cite':
            out = c
            break
    return out


def get_full_citation(title: str):
    base_url = r"https://scholar.google.de/scholar?hl=en&as_sdt=0%2C5"
    query_string = f'&q={title}'
    url = base_url + query_string
    browser = webdriver.Chrome()
    browser.get(url)
    # expand "cite"
    cite = get_cite_btn(brwsr=browser)
    cite.click()
    sleep(2)
    # click on "bib tex"
    bib_tex = browser.find_element(By.XPATH, '//*[@id="gs_citi"]/a[1]')
    bib_tex.click()
    sleep(2)
    return browser.find_element(By.XPATH, './html/body').text


def title_already_exists(bib_database, title):
    if bib_database is None:
        return False
    for entry in bib_database.entries:
        if title in entry['title']:
            return True
    return False


def make_excel(bib_text_data):
    columns = ['title', 'author', 'year', 'journal', 'booktitle', 'volume', 'number', 'pages', 'month', 'note', 'key']
    df = pd.DataFrame(columns=columns)
    for entry in bib_text_data.entries:
        df = df.append(entry, ignore_index=True)
    df['author'] = df['author'].apply(clean_latex_string)
    df['title'] = df['title'].apply(clean_latex_string)
    df['journal'] = df['journal'].apply(clean_latex_string)
    df['publisher'] = df['publisher'].apply(clean_latex_string)
    return df


def get_best_match(entry: dict, results: list):
    match_factors = list()
    for result in results:
        res_title = result.get('title', [''])[0]
        title_matcher = SequenceMatcher(None, res_title.lower(), entry['title'].lower())
        title_match = title_matcher.ratio()
        if entry.get('source') is None:
            source_match = title_match
        else:
            source = result.get('container-title', [''])[0]
            source_matcher = SequenceMatcher(None, source.lower(), entry['source'].lower())
            source_match = source_matcher.ratio()
        match_factors.append(np.mean((source_match, title_match)))
    if np.max(match_factors) < 0.9:
        print(f'WARNING: No match found for title: {entry["title"]}')
        return None
    return results[np.argmax(match_factors)]


def get_author(author_dict: dict):
    first_name = author_dict.get('given', ' ')
    last_name = author_dict.get('family', ' ')
    return f'{last_name}, {first_name[0]}.'


def get_cleaned_dict(entry: dict):
    out = dict()
    out['author'] = [get_author(auth) for auth in entry.get('author', [])]
    journal_issue = entry.get('journal-issue', '')
    if journal_issue != '':
        p_print = journal_issue.get('published-print', '')
        if p_print != '':
            out['year'] = p_print.get('date-parts', [''])[0][0]
    else:
        out['year'] = entry.get('published', '').get('date-parts', [''])[0][0]
    out['title'] = entry.get('title', [''])[0]
    source = entry.get('container-title', [''])[0]
    source.replace('&amp;', '&')
    out['source'] = source
    out['volume'] = entry.get('volume', [''])
    out['number'] = entry.get('issue', [''])
    out['pages'] = entry.get('page', [''])
    out['URL'] = entry.get('URL', [''])
    return out


if __name__ == '__main__':

    get_institute_authors()
    raise NotImplementedError('This script is not yet ready for use')
    filename_bibtex = 'iies.bib'
    filename_excel = 'iies.xlsx'

    from requests import get

    resp = get("https://api.crossref.org/works?query.bibliographic=Reliability of Running Stability during Treadmill and Overground Running")
    works = resp.json()['message']
    works = Works()
    works.query('0000-0002-0032-9936')
    works.filter(orcid='0000-0002-0032-9936')
    for work in works:
        print(work)

    path_bibtex = os.path.join(os.getcwd(), filename_bibtex)
    path_excel = os.path.join(os.getcwd(), filename_excel)

    if os.path.isfile(path_bibtex):
        with open(filename_bibtex) as bibtex_file:
            bib_database = bibtexparser.load(bibtex_file)
    else:
        bib_database = None
    entries = get_pub_titles()
    new_citations = list()
    works = Works()
    publication_list = list()
    for entry in entries:
        w_test = works.query(bibliographic=entry['title'], author=entry['authors'])
        print(f'querying for: {entry["title"]}')
        i = 0
        max_match_ratio = 0
        res = list()
        for r in w_test:
            if i > 20:
                break
            res.append(r)
            i += 1
        data = get_best_match(entry, res)
        data_clean = get_cleaned_dict(data)
        publication_list.append(data_clean)
        foo = 1

    df = pd.DataFrame(publication_list)
    # convert list of authors to string
    df['author'] = df['author'].apply(lambda x: ', '.join(x))
    df.to_excel(filename_excel, index=False)

    #     if title_already_exists(bib_database, entry):
    #         print(f'...already exists in database, skipping')
    #         continue
    #     try:
    #         citation = get_full_citation(title=entry['title'])
    #         new_citations.append(citation)
    #         with open(path_bibtex, 'a') as f:
    #             f.write(f'{citation}\n\n')
    #
    #     except Exception as e:
    #         print(e)
    #
    # df_out = make_excel(bib_database)
    # save_dataframe(df_out, path_excel)
