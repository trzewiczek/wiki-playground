import os.path
import pandas as pd
import pickle
import requests
import subprocess
import sys
import wikiparser


class DataStore(object):

    def __init__(self, lang):
        self.lang = lang

        # local paths
        self.xml_path = 'xml/{}wiki-latest-stub-meta-history.xml'.format(lang)
        self.gz_path  = 'xml/{}wiki-latest-stub-meta-history.xml.gz'.format(lang)
        self.csv_path = 'csv/{}.csv'.format(lang)
        self.md5_path = 'cache_md5sums.pickle'

        # wiki urls
        self.wiki_url = 'https://dumps.wikimedia.org/{}wiki/latest/'.format(lang)
        self.gz_url   = self.wiki_url + '{0}wiki-latest-stub-meta-history.xml.gz'.format(lang)
        self.md5_url  = self.wiki_url + '{0}wiki-latest-md5sums.txt'.format(lang)


    def get_data(self):

        if self.new_version_available() or not os.path.isfile(self.csv_path):
            self.download_xml_file()
            wikiparser.parse_xml_for(self.lang, self.csv_path, self.xml_path)

        return pd.read_csv(self.csv_path, parse_dates=['Timestamp'])


    def new_version_available(self):
        print(">>> Checking for a new version")
        return self.local_md5sum() != self.wiki_md5sum()


    def local_md5sum(self):
        # read the md5sum for a freshly downloaded .xml.gz file
        if os.path.isfile(self.gz_path):
            output = subprocess.check_output(['md5sum', self.gz_path])
            md5sum = output.decode('utf-8')[:32]

            return md5sum

        # no fresh .xml.gz file...
        else:
            # ...so read cached checksum...
            try:
                with open(self.md5_path, 'rb') as f:
                    cache_md5sums = pickle.load(f)
            except FileNotFoundError:
                # this is the first run ever, so no local checksum available
                return None

            # ...if available for this specific lang
            try:
                return cache_md5sums[self.lang]
            except KeyError:
                # this is the first run for lang, so no local checksum available
                return None


    def wiki_md5sum(self):
        # download md5sums file from wiki dumps
        response = requests.get(self.md5_url)

        if response.status_code == 404:
            print("!!! No Wikipedia for such a lang")
            print("!!! For a complete list of available Wikipedias go to: "
                  "https://en.wikipedia.org/wiki/List_of_Wikipedias#Notes")
            sys.exit(1)

        wiki_md5sums = response.text.splitlines()
        return [row[:32] for row in wiki_md5sums if 'meta-history' in row].pop()


    def download_xml_file(self):

        subprocess.call(['wget', '-O', self.gz_path, self.gz_url])
        self.update_md5sums_cache()
        subprocess.call(['gzip', '-d', '-f', self.gz_path])


    def update_md5sums_cache(self):
        try:
            with open(self.md5_path, 'rb') as f:
                cache_md5sums = pickle.load(f)
        except FileNotFoundError:
            # this is the first run of the program
            cache_md5sums = {}

        md5sum = self.local_md5sum()
        cache_md5sums[self.lang] = md5sum

        with open(self.md5_path, 'wb') as f:
            pickle.dump(cache_md5sums, f)


