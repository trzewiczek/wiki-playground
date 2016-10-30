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



def parse_xml_for(lang):
    csv_path = 'csv/{}.csv'.format(lang)
    xml_path = 'xml/{}wiki-latest-stub-meta-history.xml'.format(lang)

    print(">>> Parsing XML file")
    parser = xml.sax.make_parser()
    parser.setContentHandler(PageHandler(csv_path))
    parser.parse(xml_path)


