import pandas as pd
import threading
from cellar_extractor.eurlex_scraping import *
import json
from tqdm import tqdm
import time

"""
This is the method executed by individual threads by the add_sections method.

The big dataset is divided in parts, each thread gets its portion of work to do.
They add their portions of columns to corresponding lists, 
after all the threads are done the individual parts are put together.
"""


def execute_sections_threads(celex, eclis, start, list_sum, list_key, list_full, list_codes, list_eurovoc, list_adv,
                             list_judge, list_affecting_id, list_affecting_str,list_citations_extra, progress_bar):
    sum = pd.Series([], dtype='string')
    key = pd.Series([], dtype='string')
    full = list()
    case_codes = pd.Series([], dtype='string')
    eurovocs = pd.Series([], dtype='string')
    adv_general = pd.Series([], dtype='string')
    judge_rapporteur = pd.Series([], dtype='string')
    affecting_id = pd.Series([], dtype='string')
    affecting_str = pd.Series([], dtype='string')
    citations_extra = pd.Series([], dtype='string')
    for i in range(len(celex)):
        j = start + i
        id = celex[j]
        ecli = eclis[j]
        html = get_html_text_by_celex_id(id)
        if html != "404":
            text = get_full_text_from_html(html)
            json_text = {
                'celex': str(id),
                'ecli': ecli,
                'text': text
            }
            full.append(json_text)
        else:
            json_text = {
                'celex': str(id),
                'ecli': ecli,
                'text': ""
            }
            full.append(json_text)
        summary = get_summary_html(id)
        if summary != "No summary available":
            text = get_keywords_from_html(summary, id[0])
            text2 = get_summary_from_html(summary, id[0])
            key[j] = text
            sum[j] = text2
        else:
            key[j] = ""
            sum[j] = ""
        entire_page = get_entire_page(id)
        text = get_full_text_from_html(entire_page)
        if entire_page != "No data available":
            code = get_codes(text)
            eurovoc = get_eurovoc(text)
            adv = get_advocate_or_judge(text, "Advocate General:")
            judge = get_advocate_or_judge(text, "Judge-Rapporteur:")
            ids_affecting, strings_affecting = get_case_affecting(text)
            citation_extra = get_citations_with_extra_info(text)
        else:
            code = ""
            eurovoc = ""
            adv = ""
            judge = ""
            ids_affecting = ""
            strings_affecting = ""
            citation_extra = ""

        eurovocs[j] = eurovoc
        case_codes[j] = code
        adv_general[j] = adv
        affecting_id[j] = ids_affecting
        affecting_str[j] = strings_affecting
        judge_rapporteur[j] = judge
        citations_extra[j] = citation_extra
        progress_bar.update(1)

    list_sum.append(sum)
    list_key.append(key)
    list_full.append(full)
    list_codes.append(case_codes)
    list_eurovoc.append(eurovocs)
    list_adv.append(adv_general)
    list_judge.append(judge_rapporteur)
    list_affecting_id.append(affecting_id)
    list_affecting_str.append(affecting_str)
    list_citations_extra.append(citations_extra)

"""
This method adds the following sections to a pandas dataframe, as separate columns:

Full Text
Case law directory codes
Keywords
Summary
Advocate General
Judge Rapporteur
Case affecting (CELEX ID)
Case affecting string (entire str with more info)

Method is cellar-specific, scraping html from https://eur-lex.europa.eu/homepage.html.
It operates with multiple threads, using that feature is recommended as it speeds up the entire process.
"""


def add_sections(data, threads, json_filepath=None):
    celex = data.loc[:, 'CELEX IDENTIFIER']
    eclis = data.loc[:, 'ECLI']
    length = celex.size
    time.sleep(1)
    bar = tqdm(total=length, colour="GREEN", miniters=int(length/100), position=0, leave=True, maxinterval=10000)
    if length > threads:  # to avoid getting problems with small files
        at_once_threads = int(length / threads)
    else:
        at_once_threads = length
    threads = []
    list_sum = list()
    list_key = list()
    list_full = list()
    list_codes = list()
    list_eurovoc = list()
    list_adv = list()
    list_judge = list()
    list_affecting_id = list()
    list_affecting_str = list()
    list_citations_extra = list()
    for i in range(0, length, at_once_threads):
        curr_celex = celex[i:(i + at_once_threads)]
        curr_ecli = eclis[i:(i + at_once_threads)]
        t = threading.Thread(target=execute_sections_threads,
                             args=(
                                 curr_celex, curr_ecli, i, list_sum, list_key, list_full, list_codes, list_eurovoc,
                                 list_adv, list_judge, list_affecting_id, list_affecting_str,list_citations_extra, bar))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    add_column_frow_list(data, "celex_summary", list_sum)
    add_column_frow_list(data, "celex_keywords", list_key)
    add_column_frow_list(data, "celex_eurovoc", list_eurovoc)
    add_column_frow_list(data, "celex_directory_codes", list_codes)
    add_column_frow_list(data, 'advocate_general', list_adv)
    add_column_frow_list(data, 'judge_rapporteur', list_judge)
    add_column_frow_list(data, 'affecting_ids', list_affecting_id)
    add_column_frow_list(data, 'affecting_strings', list_affecting_str)
    add_column_frow_list(data, 'citations_extra_info',list_citations_extra)
    if json_filepath:
        with open(json_filepath, 'w', encoding='utf-8') as f:
            for l in list_full:
                if len(l) > 0:
                    json.dump(l, f)
    else:
        json_file = []
        for l in list_full:
            if len(l) > 0:
                json_file.extend(l)
        return json_file


"""
Used for adding columns easier to a dataframe for add_sections().
"""


def add_column_frow_list(data, name, list):
    column = pd.Series([], dtype='string')
    for l in list:
        column = column.append(l)
    column.sort_index(inplace=True)
    data.insert(1, name, column)
