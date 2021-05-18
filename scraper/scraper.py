#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Created: 4th November 2020
# Authors: Jerome Wynne (jeromewynne@das-ltd.co.uk)
#          Mark Drakeford (began __write_vacancy_urls_to_file)
# Environment: wmchack
# Summary: Scrapes job descriptions from the NHS Jobs
#          website and writes them to a JSON list.
# Contents:
#   fnc scrape_vacancies
#   fnc __graceful_request_to_soup
#   fnc __write_vacancy_urls_to_file
#   fnc __write_vacancies_to_json
#   fnc __write_vacancy_to_json
#   fnc __write_json_to_feather

import requests
import bs4 as bs
import json
from glob import glob
import pandas as pd
from time import sleep
import logging
import os
import re
from math import ceil

TIME_BETWEEN_UNSUCCESSFUL_REQUESTS = 10 # seconds
TIMEOUT = 10 # requests.get timeout, seconds
JOBS_PER_PAGE = 20.
STATE_URLS = '0'
STATE_JSON = '1'
STATE_FEATHER = '2'
STATE_END = '3'


def scrape_vacancies(scrape_id: str, cookie: str):
    ''' Scrapes vacancy descriptions from NHS Jobs to a Feather dataframe.

    Refer to /tmp/scrape_id.log for updates on scrape progress.

    Because the scrape takes several hours, scrape_vacancies is 
    designed to recover existing scrape progress if interrupted.
    To recover existing progess, call
        scrape_vacancies(scrape_id)
    using the scrape_id of the scrape that was interrupted.

    The status of a scrape is tracked via file ../data/scrape_id.status.
    Status codes:
        0: scraping vacancy descriptions urls to vacancy_page_urls.csv
        1: scraping vacancy descriptions from urls to .json files
        2: merging .json files into dataframe and writing to Feather
        3: scrape complete

    Args:
        scrape_id: uniquely identifies the scrape. A good choice is 
                   str(int(time.time())).
        cookie: string containing cookie for NHS Jobs search
                (refer to example.py for further info).

    Returns:
        nothing

    Files output:
        ./data/scrape_id/json/*.json
        ./data/scrape_id/vacancy_page_urls.csv
        ./data/scrape_id/ignored_vacancy_page_urls.csv
        ./data/scrape_id/vacancy_descriptions.feather
        ./tmp/scrape_id.log
        ./tmp/scrape_id.state
        ./tmp/scrape_id_page.tmp
    '''
    # check if required directories exist (make it if not)
    dirs = [
            os.path.join('.', 'data'),
            os.path.join('.', 'data', scrape_id),
            os.path.join('.', 'tmp')
    ]
    for dir_path in dirs:
        if not os.path.exists(dir_path): os.mkdir(dir_path)

    # configure log
    log_path = os.path.join('.', 'tmp', scrape_id + '.log')
    logging.basicConfig(filename=log_path, level=logging.INFO,
        format='%(asctime)s:%(filename)s:%(funcName)s: %(message)s')
    logging.info('Scraper \'{}\' intialized.'.format(scrape_id))

    # check if scrape has previously been started/completed
    state_fp = os.path.join('.', 'tmp', scrape_id + '.state')
    try:
        with open(state_fp, 'r', encoding='utf-8') as state_f:
            state = state_f.read()
    except FileNotFoundError:
        state = STATE_URLS # enter first state
        with open(state_fp, 'w', encoding='utf-8') as state_f:
            state_f.write(state)

    logging.info('Entered state {}'.format(state))

    switchboard = { # maps states to functions
        STATE_URLS: __write_vacancy_urls_to_file, # scrape URLs from search results
        STATE_JSON: __write_vacancies_to_json, # scrape JSON at URLs
        STATE_FEATHER: __write_json_to_feather # write JSON to Feather
    } # each function returns state of next stage of scrape

    while state != STATE_END:
        state = switchboard[state](scrape_id, cookie)
        with open(state_fp, 'w', encoding='utf-8') as state_f:
            state_f.write(state)
        logging.info('Entered state {}. Updated {}.'.format(
            state, state_fp))

    logging.info('Scrape \'{}\' complete.'.format(scrape_id))


def __graceful_request_to_soup(url: str, cookie:str):
    ''' requests.get that handles errors, retries.

        Returns:
            bs.BeautifulSoup: is bs.Beatifulsoup(requests.get(url))

        Will retry until request is successful.
    '''
    header = {'cookie':cookie}

    try:
        r = requests.get(url, timeout=TIMEOUT, headers=header)
        logging.info('Request status code is {}.'.format(r.status_code))
        soup = bs.BeautifulSoup(r.text, 'html.parser')

    except (requests.exceptions.ConnectionError,
            requests.exceptions.ConnectTimeout, 
            requests.exceptions.ReadTimeout):
        logging.info('Request error thrown, retrying in 60 seconds...')
        sleep(TIME_BETWEEN_UNSUCCESSFUL_REQUESTS) # wait a bit before retrying
        soup = __graceful_request_to_soup(url, cookie)
    return soup


def __write_vacancy_urls_to_file(scrape_id: str, cookie:str):
    ''' Writes vacancy URLs from NHS Jobs search results pages to file.

        URLs are scraped from pages like
            https://www.jobs.nhs.uk/xi/search_vacancy?action=page&page=1

        Returns:
            int: STATE_JSON
    '''
    urls_fp = os.path.join('.', 'data', scrape_id, 'vacancy_page_urls.csv')
    urls_tmp_fp = os.path.join('.', 'tmp', scrape_id + '_page.tmp') # tracks n_pages,
                                                                    # pages_read

    search_url_prefix = 'https://www.jobs.nhs.uk/xi/search_vacancy?action=page&page='

    try: # if urls_scrape_id.tmp exists, contains 'n_pages,last_page_scraped'
        with open(urls_tmp_fp, 'r', encoding='utf-8') as f:
            s = f.read()
            n_pages, start_page_n = [int(v) for v in s.split(',')]
            start_page_n += 1

    except FileNotFoundError: # if urls_scrape_id.tmp does not exist
        page1_url = search_url_prefix + str(1)
        logging.info('Getting page count from page {}.'.format(page1_url))
        soup = __graceful_request_to_soup(page1_url, cookie)
        job_count_txt = soup.find('span', class_='jobCount').get_text()
        job_count = float(re.sub('[^0-9]', '', job_count_txt))
        n_pages = ceil(job_count/JOBS_PER_PAGE)
        logging.info('Determined that there are {} pages to iterate over.'
                        .format(n_pages))
        start_page_n = 1

    # iterate over pages of NHS Jobs search results,
    # writing URLs of pages to file
    for page_n in range(start_page_n, n_pages+1):
        logging.info('Scraping URLs from page {} of {}.'.format(page_n,
                                                                n_pages))

        # get page page_n of search results
        soup = __graceful_request_to_soup(search_url_prefix + str(page_n),
                                          cookie)

        # use bs to get vacancy page URLs
        for v in soup.find_all('div', attrs={'class':'vacancy'}):
            rel_path = v.find('h2').find('a')['href']

            # write vacancy page URL to file
            with open(urls_fp, 'a', encoding='utf-8') as f:
                f.write('https://www.jobs.nhs.uk' + rel_path + '\n')

        if page_n < n_pages: # update number of last page scraped
            with open(urls_tmp_fp, 'w', encoding='utf-8') as f:
                f.write(str(n_pages) + ',' + str(page_n))
        if page_n == n_pages: # delete urls_scrape_id.tmp
            os.remove(urls_tmp_fp)
            logging.info('All vacancy page URLs scraped successfully.')

    return STATE_JSON


def __write_vacancies_to_json(scrape_id: str, cookie: str):
    ''' Writes vacancy descriptions and metadata to JSON files.

        Vacancy descriptions and metadata are scraped from pages like
            https://www.jobs.nhs.uk/xi/vacancy/916249731
        A vacancy's ID is the number at the tail of its URL.
    
        Returns:
            int: STATE_FEATHER
    '''
    # make directory for json files if it doesn't already exist
    json_dir = os.path.join('.', 'data', scrape_id, 'json', '')
    try:
        os.mkdir(json_dir)
    except FileExistsError:
        pass
    
    urls_fp = os.path.join('.', 'data', scrape_id, 
                           'vacancy_page_urls.csv')

    logging.info('Scraping vacancy pages based on URLs in {}.'.format(urls_fp))
    
    # get vacancy ids for vacancies that have already been captured or ignored
    captured_ids = set([os.path.split(v)[-1][:-5] 
                                    for v in glob(json_dir + '*.json')])
    ignored_ids_fp = os.path.join('.', 'data', scrape_id,
                                  'ignored_vacancy_page_urls.csv')
    try: # get vacancy ids that have already been ignored
        with open(ignored_ids_fp, 'r', encoding='utf-8') as f:
            ignored_ids = set(f.read().split('\n'))
    except FileNotFoundError:
        ignored_ids = set()

    ids_to_skip = captured_ids.union(ignored_ids)

    # load urls to scrape descriptions from
    with open(urls_fp, 'r', encoding='utf-8') as urls_file:
        list_of_urls = urls_file.read().splitlines()
        n_urls = len(list_of_urls)
    
    # iterate over urls, scraping vacancy descriptions and metadata
    for j, page_url in enumerate(list_of_urls):
        logging.info('Scraping vacancy description page {} of {}.'.format(j+1,
                                                                     n_urls))
        page_id = page_url.split('/')[-1] # is a string
        if page_id not in ids_to_skip: 
            try:
                __write_vacancy_to_json(dst_dir=json_dir,
                                        page_id=page_id,
                                        cookie=cookie) # download
            except AttributeError: # occurs if page isn't structured correctly
                # add id to ignored ids
                with open(ignored_ids_fp, 'a', encoding='utf-8') as f:
                    f.write(page_id + '\n')
                logging.info('Page format incorrect, appending page id' \
                             ' to {} and skipping.'.format(ignored_ids_fp))
                continue # move on to next page_url
        else: # vacancy json has already been saved/ignored
            logging.info('Skipping vacancy page {}.'.format(page_id))

    return STATE_FEATHER


def __write_vacancy_to_json(dst_dir: str, page_id: str, cookie: str):
    ''' Parses a vacancy description web page and writes its fields
        to a JSON file.

        Returns:
            nothing
    '''
    url = ' https://www.jobs.nhs.uk/xi/vacancy/' + page_id
    logging.info('Scraping vacancy description at {}.'.format(url))
    soup = __graceful_request_to_soup(url, cookie)
    json_str = soup.find('script', # job description in JSON 
                          attrs={'id':'jobPostingSchema'}).contents[0]
    page_dct = json.loads(json_str)
    with open(dst_dir + page_id + '.json', 'w', encoding='utf-8') as f:
        json.dump(page_dct, f)


def __write_json_to_feather(scrape_id: str, _: str):
    ''' Reads all .json files in ./data/scrape_id/json/ into dataframe,
        saves dataframe in Feather format.

        Returns STATE_END.
    '''
    logging.info('Initialized write of JSON files to Feather dataframe.')

    json_dir = os.path.join('.', 'data', scrape_id, 'json', '')
    json_fps = glob(json_dir + '*.json')
    list_of_page_dct = []
    for fp in json_fps: # read all of the json files into a list of dicts
        with open(fp, 'r', encoding='utf-8') as f:
            list_of_page_dct += [json.load(f)]
    
    # flatten the list of dicts to a DataFrame
    df = pd.json_normalize(list_of_page_dct)

    # write it to a Feather file
    dst_fp = os.path.join('.', 'data', scrape_id, 
                          'vacancy_descriptions.feather')
    df.to_feather(dst_fp)
    logging.info('Wrote JSON files to Feather dataframe at {}.'.format(dst_fp))

    return STATE_END
