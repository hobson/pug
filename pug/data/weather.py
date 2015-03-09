import os
import urllib
from StringIO import StringIO
import re

import pandas as pd

DATA_PATH = os.path.dirname(os.path.realpath(__file__))

# fresno = pd.DataFrame.from_csv(os.path.join(DATA_PATH, 'weather_fresno.csv'))

def airport(location='Fresno, CA', date='2012/1/1', verbosity=1):
    suffix = '/CustomHistory.html?dayend=1&monthend=1&yearend=2015&req_city=&req_state=&req_statename=&reqdb.zip=&reqdb.magic=&reqdb.wmo=&MR=1&format=1'
    prefix = 'http://www.wunderground.com/history/'
    url = prefix + 'airport/' + airport.locations.get(location, location) + '/' + date + suffix
    if verbosity:
        print('GETing csv from "{0}"'.format(url))
    buf = urllib.urlopen(url).read()
    if verbosity:
        N = buf.count('\n')
        M = (buf.count(',') + N) / float(N)
        print('Retrieved CSV with appox. {0} lines, {2} columns, or {1} cells.'.format(N, int(M * N), M))

    try:
        df = pd.DataFrame.from_csv(StringIO(buf))
    except IndexError:
        table = [row.split(',') for row in buf.split('\n') if len(row)>1]
        numcols = max(len(row) for row in table)
        table = [row for row in table if len(row) == numcols]
        df = pd.DataFrame(table)
        df.columns = [str(label) for label in df.iloc[0].values]
        df = df.iloc[1:]
    df.columns = [label.strip() for label in df.columns]
    print df.columns
    print type(df.columns)
    columns = df.columns.values
    print columns
    columns = re.sub(r'<br\s*[/]?>','', columns[-1])
    print columns
    df.columns = columns

    for i, obj in enumerate(df[df.columns[-1]]):
        try:
            df[df.columns[-1]].iloc[i] = re.sub(r'<br\s*[/]?>','', obj)
            try:
                df[df.columns[-1]].iloc[i] = int(df[df.columns[-1]].iloc[i])
            except:
                try:
                    df[df.columns[-1]].iloc[i] = float(df[df.columns[-1]].iloc[i])
                except:
                    pass
        except:
            pass
    if verbosity > 1:
        print(df)
    return df
airport.locations = dict([(str(city) + ', ' + str(region)[-2:], str(ident)) for city, region, ident in pd.DataFrame.from_csv(os.path.join(DATA_PATH, 'airports.csv')).sort(ascending=False)[['municipality', 'iso_region', 'ident']].values])
