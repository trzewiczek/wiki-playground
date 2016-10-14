# coding: utf-8

import pandas as pd
import sys
import xml.etree.ElementTree as ET


## setup the stage
try:
    LANG = sys.argv[1]
except IndexError:
    print("!!! No wiki language code specified")
    print("--- python parse_xml.py <lang_code>")

    sys.exit(1)

FILE_NAME = LANG + 'wiki-latest-stub-meta-history'
FILE_GZ   = FILE_NAME + '.xml.gz'
FILE_XML  = 'xml/' + FILE_NAME + '.xml'
FILE_CSV  = 'csv/' + FILE_NAME + '.csv'
DUMP_URL  = 'https://dumps.wikimedia.org/{}wiki/latest/{}'.format(LANG, FILE_GZ)
WIKI_NS   = '{http://www.mediawiki.org/xml/export-0.10/}'

def tag(tag_name):
    """Add Wikipedia Namespace to a <tag_name>"""
    return WIKI_NS + tag_name

def xp(tag_name):
    """Inject Wikipedia Namespace into XPath for a specific <tag_name>"""
    return './/' + WIKI_NS + tag_name

# TODO manage memory more efficient

## extract pages tags from XML file
try:
    xml = open(FILE_XML, 'rb')
except FileNotFoundError:
    print("!!! No XML file found. Try to download one.")

    import subprocess

    print(">>> Downloading file from {}".format(DUMP_URL))
    subprocess.call(['wget', '-O', 'xml/' + FILE_GZ, DUMP_URL])
    subprocess.call(['gzip', '-d', 'xml/' + FILE_GZ])

    xml = open(FILE_XML, 'rb')

print('>>> Parsing XML file')
tree = ET.parse(xml)
root  = tree.getroot()
pages = [el for el in root.iter(tag('page'))]

## collect the data
# name 'Contributor' is used instead of 'User',
# because sometimes it's just a plain IP or event MAC address
columns = ['ID', 'Title', 'Timestamp', 'Contributor', 'Quota']
data    = []

print('>>> Extracting data from {} pages'.format(len(pages)))
for page in pages:
    page_id    = page.find(tag('id')).text
    page_title = page.find(tag('title')).text

# TODO extract information about whether or not a revision is a page creation
    for revision in page.findall(tag('revision')):
        timestamp = revision.find(tag('timestamp')).text
        quota     = revision.find(tag('text')).get('bytes')
        try:
            contributor = revision.findall(xp('username')).pop().text
        except IndexError:
            contributor = revision.findall(xp('ip')).pop().text

        data.append({
            'ID'         : page_id,
            'Title'      : page_title,
            'Timestamp'  : timestamp,
            'Contributor': contributor,
            'Quota'      : quota
            })


## save data into csv
print('>>> Saving data into {} file'.format(FILE_CSV))
df = pd.DataFrame(data, columns=columns)
df.to_csv(FILE_CSV, index=False)

