from glob import glob
import json
import unicodedata
import html
import re
import os
import pandas as pd
from tqdm import tqdm

def clean_text(s: str) -> str:
    """ For cleaning the "description" field of an NHS Jobs record.
    """
    s = unicodedata.normalize("NFKD", s) # simplify unicode of string
    s = html.unescape(s) # convert html entities to unicode characters
    s = re.sub(r"(</p>|</li>)", "\n", s) # replace p or li close with newline 
    s = re.sub(r"<li>", "• ", s) # replace list item start with bullets
    s = re.sub(r"<[^<]+?>", "", s) # otherwise strip HTML tags
    return s

def load_corpus(return_as_df=True):
    """ Returns a dictionary/pandas DataFrame where each entry corresponds to 
        one NHS Jobs record.
    """
    filepaths = glob(os.path.join(".", "data", "*.json"))
    data = {}
    for fp in tqdm(filepaths):
        with open(fp, "r") as f: record_dct = json.load(f)
        entry_id = record_dct["url"].split("/")[-1]
        desc = clean_text(record_dct["description"])
        data[entry_id] = {
            "title": clean_text(record_dct["title"]),
            "text-raw": record_dct["description"],
            "text-clean": desc,
            "fileid": int(entry_id),
            "postcode": record_dct["jobLocation"]["address"]["postalCode"],
            "lon": record_dct["jobLocation"]["geo"]["longitude"],
            "lat": record_dct["jobLocation"]["geo"]["latitude"],
            "hiring-org": record_dct["hiringOrganization"]["name"]
        } 

    if return_as_df: 
        return pd.DataFrame.from_dict(data, orient="index")
    else:
        return data

def extract_tfidf(file_contents: list):
    """
    Args:
        file_contents: list of strings

    Returns:
        sparse tfidf numpy array 
    """ 
    # returns tfidf matrix as coo sparse 
    
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    min_df = 1 # ignore tokens that appear in only one file
    max_df = 0.25 # ignore tokens that appear in more than 90% of files
    
    vectorizer = TfidfVectorizer(input = file_contents,
                    strip_accents = "unicode",
                    lowercase = True,
                    ngram_range = (1, 1),
                    analyzer = "word",
                    max_df = max_df, # ignore terms that appear in more than this prop. of docs,
                    min_df = min_df,
                    stop_words = "english", # can pass custom list
                    norm = "l2", # scale rows to unit norm
                    use_idf = True,
                    smooth_idf = True, # add 1 to document frequencies
                    sublinear_tf = False # replace tf with 1 + log(tf)
                   )
    # attributes of vectorizer:
    #     vocabulary_ -> dict mapping terms to feature indices
    #     idf_ -> inverse document frequency vector
    #     stop_words -> list of words ignored
    s_tfidf = vectorizer.fit_transform(file_contents) # row-normalized tfidf matrix (sparse)
    
    return s_tfidf