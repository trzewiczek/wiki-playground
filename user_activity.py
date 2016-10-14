# coding: utf-8

import pandas as pd
import re
import sys

from datetime   import date
from datetime   import datetime as dt
from matplotlib import pyplot   as plt


## setup the stage
try:
    LANG = sys.argv[1]
except IndexError:
    print("!!! No wiki language code specified")
    print("--- python parse_xml.py <lang_code>")

    sys.exit(1)

FILE_CSV = 'csv/' + LANG + 'wiki-latest-stub-meta-history.csv'

print('>>> Reading {} file'.format(FILE_CSV))
data = pd.read_csv(FILE_CSV, parse_dates=['Timestamp'])

## Extract only data needed for analysis
# keep only identifiable users, i.e. no IP or MAC addresses or bots
re_ip  = re.compile('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
re_mac = re.compile('^([0-9A-Fa-f]{1,4}[:]){7}([0-9A-Fa-f]{1,4})$')
re_bot = re.compile('bot$', re.I)

# TODO test if this needs optimizattion for bigger files (no for 200k rows)
print('>>> Cleaning up the data')
ips  = data.Contributor.str.match(re_ip)
macs = data.Contributor.str.match(re_mac)  # --> no actual boolean list, but ok
bots = data.Contributor.str.contains(re_bot)
wiki = data.Contributor.str.contains('MediaWiki')
code = data.Contributor.str.match('CommonsDelinker')
meta = data.Title.str.contains(':')

columns = ['Contributor', 'Timestamp']
date_user = data[~(ips | macs | bots | wiki | code | meta)][columns]

print('>>> Wrangling the data')
# extract date from timestamp
date_user['Date'] = [dt.date(x) for x in date_user['Timestamp']]
date_user.drop('Timestamp', axis=1, inplace=True)
date_user.drop_duplicates(inplace=True)

## Contributions frequency in days active
num_edits = date_user.groupby('Contributor').size()
# TODO make 25 a statistics-based number (i.e. use brainss)!
num_edits = num_edits[num_edits >= 25]  # c'mon, at least 25 edits in 10 years!

print('>>> Plotting results')
users = num_edits.sort_values().index.tolist()
for i, user in enumerate(users, 1):
    dates = date_user[date_user.Contributor.str.match(user)]['Date'].tolist()

    plt.plot(dates, [i] * len(dates), '.')


plt.xlim(date(date_user.Date.min().year,1,1), date(2016,12,31))

# ylim starts with 0 and ends at # of users+1 just to get an extra margin
plt.ylim(0, len(users)+1)
plt.yticks(range(len(users)+2), ['']+users+[''])

plt.title("Top {0} contributors".format(len(users)))

# TODO save to png/pdf vs show via args parameter
plt.show()

