# coding: utf-8

# TODO add some logs, so it's clear the script is working fine

import xml.etree.ElementTree as ET
import pandas as pd

# TODO get language code from agrs and download latest file if one not present

# setup the stage
FILE_NAME = 'szlwiki-latest-stub-meta-history'
WIKI_NS   = '{http://www.mediawiki.org/xml/export-0.10/}'

def tag(tag_name):
    """Add Wikipedia Namespace to a <tag_name>"""
    return WIKI_NS + tag_name

def xp(tag_name):
    """Inject Wikipedia Namespace into XPath for a specific <tag_name>"""
    return './/' + WIKI_NS + tag_name

# TODO manage memory more efficient

# extract pages tags from XML file
tree  = ET.parse('xml/' + FILE_NAME + '.xml')
root  = tree.getroot()
pages = [el for el in root.iter(tag('page'))]

# collect the data
# name 'Contributor' is used instead of 'User',
# because sometimes it's just a plain IP or event MAC address
columns = ['ID', 'Title', 'Timestamp', 'Contributor', 'Quota']
data    = []

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


# save data into csv file via Pandas DataFrame
df = pd.DataFrame(data, columns=columns)
df.to_csv('csv/' + FILE_NAME + '.csv', index=False)

