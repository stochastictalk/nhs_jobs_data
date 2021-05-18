#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Created: 6th November 2020 (updated May 2021)
# Author: Jerome Wynne (jeromewynne@das-ltd.co.uk)
# Environment: nhs_jobs_data
# Summary: Demo of how to use scraper.py.

# To scrape NHS Jobs you need a cookie that identifies your search.
# You can get this cookie by following these steps.
# 1. Open your web browser and go to www.jobs.nhs.uk.
# 2. Click 'Accept all cookies'.
# 3. Specify your search terms then press 'Search'.
# 4. You will see the first page of search results. In your browser,
#    open Developer Tools > Network, then refresh the page by pressing F5.
# 5. You should see the Network pane populate with HTTP exchanges,
#    the first of which will be called 'search_vacancy/'. Click on it.
# 6. In the 'Headers' frame, scroll down to 'Request Headers' and find
#    the field 'cookie'. Copy its value.
# 7. Pass the cookie to scrape_vacancies() as a string.

from scraper import scrape_vacancies

scrape_id: str = 'example'
# you may need to replace this cookie by following the instructions above!
cookie = r'cookies_settings={"usage":"true","essential":"true","version":3,"pixel_tracking":"true","origin_tracking":"true"}; _ga=GA1.3.941869833.1613561401; _gid=GA1.3.1531939925.1621260424; general_session=29382D5EB71911EBB2C03128B1AAC5B6; _gat_gtag_UA_3320079_1=1'
scrape_vacancies(scrape_id, cookie)

# To monitor scrape progress, open ./tmp/example.log in VS Code, or any other
# text editor that will update as the file is written to by another program.

# scrape_vacancies() can recover progress if for any reason it is interrupted.
# Read the scrape_vacancies() docstring in scraper.py to see how to do this.