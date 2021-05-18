# NHS Jobs Data

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
