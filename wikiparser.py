# coding: utf-8

import pandas as pd
import sys
import xml.sax


class PageHandler(xml.sax.ContentHandler):

    def __init__(self, output_file):
        self.output_file = output_file

        # content based tags
        self.tags = {
                'page'     : False,
                'id'       : False,
                'revision' : False,
                'title'    : False,
                'timestamp': False,
                'username' : False,
                'ip'       : False,
            }

        # data to be collected
        # all content based tags' fields are buffers (lists) due to problem
        # with xml.sax module's ContentHandler.characters function that
        # sometimes consumes text content in chunks. For that reason text is
        # buffered and then flushed with ''.join(buffer) for final shape.
        self.data = {
                'ID'         : [],
                'Title'      : [],
                'Timestamp'  : [],
                'Contributor': [],
                'Quota'      : '',  # hack with join() in endElement!
            }

        self.all_data = []


    def startElement(self, name, attrs):
        if name in self.tags.keys():
            self.tags[name] = True

        if name == 'text':
            self.data['Quota'] = attrs.get('bytes', '')


    def endElement(self, name):
        if name in self.tags.keys():
            self.tags[name] = False

        if name == 'revision':
            self.all_data.append({
                k: ''.join(v) for k, v in self.data.items()
            })
            # clean up only revision related data -- keep ID untouched
            self.data['Timestamp']   = []
            self.data['Contributor'] = []
            self.data['Quota']       = ''

        if name == 'page':
            self.data['ID']    = []
            self.data['Title'] = []


    def characters(self, content):
        if self.tags['id'] and not self.tags['revision']:
            self.data['ID'].append(content)

        if self.tags['title']:
            self.data['Title'].append(content)

        if self.tags['timestamp']:
            self.data['Timestamp'].append(content)

        if self.tags['username'] or self.tags['ip']:
            self.data['Contributor'].append(content)


    def endDocument(self):
        print('>>> Saving CSV file')
        columns = ['ID', 'Title', 'Timestamp', 'Contributor', 'Quota']
        df = pd.DataFrame(self.all_data, columns=columns)
        df.to_csv(self.output_file, index=False)


def prepare_csv_for(lang):
    FILE_NAME = lang + 'wiki-latest-stub-meta-history'
    FILE_GZ   = FILE_NAME + '.xml.gz'
    FILE_XML  = 'xml/' + FILE_NAME + '.xml'
    FILE_CSV  = 'csv/' + lang + '.csv'
    DUMP_URL  = 'https://dumps.wikimedia.org/{}wiki/latest/{}'.format(lang, FILE_GZ)
    WIKI_NS   = '{http://www.mediawiki.org/xml/export-0.10/}'
    try:
        xml_fh = open(FILE_XML, 'rb')
        print('>>> XML file found')
    except FileNotFoundError:
        print("!!! No XML file found. Trying to download one.")

        import subprocess

        print(">>> Downloading file from {}".format(DUMP_URL))
        subprocess.call(['wget', '-O', 'xml/' + FILE_GZ, DUMP_URL])
        subprocess.call(['gzip', '-d', 'xml/' + FILE_GZ])

        xml_fh = open(FILE_XML, 'rb')

    print('>>> Parsing XML file')
    parser = xml.sax.make_parser()
    parser.setContentHandler(PageHandler(FILE_CSV))
    parser.parse(xml_fh)


