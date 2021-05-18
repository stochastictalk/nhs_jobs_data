# NHS Jobs Data

This repo contains two things: a web scraper for the NHS Jobs website (http://www.jobs.nhs.uk/), and an instance of the dataset that this scraper generates.

## Prerequisite: `conda` virtual environment

To use the Python scripts in this repo you need to install some dependencies. `requirements.txt` lists these for Windows. I don't know whether these requirements will be sufficient for Mac/Linux (probably not).

In the command line (e.g. Command Prompt, PowerShell), run
```
conda create --name nhs_jobs_data --file requirements.txt
```
to create a conda environment from `requirements.txt`. You should then run Python in the context of this virtual environment by activiating it:
```
conda activate nhs_jobs_data
```

## Example Dataset

`data/` contains 14,842 records scraped from the NHS Jobs website in early November 2020.

The function `load_corpus()` in `load.py` loads the records from the JSON files into a Pandas DataFrame.

A row in this DataFrame corresponds to a single record with attributes:
* `title`: the title of the vacancy.
* `text-raw`: the free-text HTML description of the vacancy.
* `text-clean`: same as `text-raw`, but with HTML entities either removed or converted to Unicode characters.
* `fileid`: ID of record (same as key of parent dictionary).
* `postcode`: postcode of the hiring organisation.
* `lon`, `lat`: longitude and latitude coordinates of hiring organisation.
* `hiring-org`: name of the hiring organisation. 

`load.py` also contains convenience function `extract_tfidf()`, which returns the term frequency-inverse document frequency matrix of a list of strings.

To generate the tfidf matrix of the cleaned job descriptions, you could run something like:
```python
df = load_corpus(return_as_df = True)
list_of_job_descriptions = df["text-clean"].to_list()
s_tfidf = extract_tfidf(list_of_job_descriptions) # tfidf matrix
```

## Scraper

Run `python example.py` to scrape the records from the NHS Jobs website. If it fails, you may need to change the cookie it uses - edit `example.py` according to its instructions to do this. You can scrape a subset of records by following the instructions for changing the cookie.
