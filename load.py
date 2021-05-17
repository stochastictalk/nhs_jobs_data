from glob import glob
import json
import unicodedata
import html
import re
import os
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

def load_corpus() -> dict:
    """ Returns a dictionary where each entry corresponds to one NHS
        Jobs record.
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

    return data

data = load_corpus()
#spacy_stopwords = spacy.load("en_core_web_sm").Defaults.stop_words
