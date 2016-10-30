import os.path
import pandas as pd
import pickle
import requests
import subprocess
import sys
import wikiparser

# local paths
XML_PATH  = 'xml/{}wiki-latest-stub-meta-history.xml'
GZ_PATH   = 'xml/{}wiki-latest-stub-meta-history.xml.gz'
CSV_PATH  = 'csv/{}.csv'
MD5_PATH  = 'cache_md5sums.pickle'
# wiki urls
WIKI_URL = 'https://dumps.wikimedia.org/{0}wiki/latest/'
GZ_URL   = WIKI_URL + '{0}wiki-latest-stub-meta-history.xml.gz'
MD5_URL  = WIKI_URL + '{0}wiki-latest-md5sums.txt'


def get_data_for(lang):
    csv_path = CSV_PATH.format(lang)

    if new_version_available_for(lang) or not os.path.isfile(csv_path):
        download_xml_file_for(lang)
        wikiparser.parse_xml_for(lang)

    return pd.read_csv(csv_path, parse_dates=['Timestamp'])


def new_version_available_for(lang):
    print(">>> Checking for a new version")
    return local_md5sum_for(lang) != wiki_md5sum_for(lang)


def local_md5sum_for(lang):
    gz_path  = GZ_PATH.format(lang)
    md5_path = MD5_PATH.format(lang)

    # read the md5sum for a freshly downloaded .xml.gz file
    if os.path.isfile(gz_path):
        return subprocess.check_output(['md5sum', gz_path]).decode('utf-8')[:32]

    # no fresh .xml.gz file...
    else:
        # ...so read cached checksum...
        try:
            with open(md5_path, 'rb') as f:
                cache_md5sums = pickle.load(f)
        except FileNotFoundError:
            # this is the first run ever, so no local checksum available
            return None

        # ...if available for this specific lang
        try:
            return cache_md5sums[lang]
        except KeyError:
            # this is the first run for lang, so no local checksum available
            return None


def wiki_md5sum_for(lang):
    md5_url = MD5_URL.format(lang)
    response = requests.get(md5_url)

    if response.status_code == 404:
        print("!!! No Wikipedia for such a lang")
        print("!!! For a complete list of available Wikipedias go to: "
              "https://en.wikipedia.org/wiki/List_of_Wikipedias#Notes")
        sys.exit(1)

    wiki_md5sums = response.text.splitlines()
    return [row[:32] for row in wiki_md5sums if 'meta-history' in row].pop()


def download_xml_file_for(lang):
    gz_url  = GZ_URL.format(lang)
    gz_path = GZ_PATH.format(lang)

    subprocess.call(['wget', '-O', gz_path, gz_url])
    update_md5sums_cache_for(lang)
    subprocess.call(['gzip', '-d', '-f', gz_path])


def update_md5sums_cache_for(lang):
    md5_path = MD5_PATH.format(lang)
    try:
        with open(md5_path, 'rb') as f:
            cache_md5sums = pickle.load(f)
    except FileNotFoundError:
        # this is the first run of the program
        cache_md5sums = {}

    md5sum = local_md5sum_for(lang)
    cache_md5sums[lang] = md5sum

    with open(md5_path, 'wb') as f:
        pickle.dump(cache_md5sums, f)


