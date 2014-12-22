import re
import os
import csv
import datetime

from dateutil.parser import parse as parse_date

import pandas as pd

# date and datetime separators
COLUMN_SEP = re.compile(r'[,/;]')


def make_dataframe(prices, num_prices=1, columns=('portfolio',)):
    """Convert a file, list of strings, or list of tuples into a Pandas DataFrame

    Arguments:
      num_prices (int): if not null, the number of columns (from right) that contain numeric values
    """
    if isinstance(prices, pd.Series):
        return pd.DataFrame(prices)
    if isinstance(prices, pd.DataFrame):
        return prices
    if isinstance(prices, basestring) and os.path.isfile(prices):
        prices = open(prices, 'rU')
    if isinstance(prices, file):
        values = []
        # FIXME: what if it's not a CSV but a TSV or PSV
        csvreader = csv.reader(prices, dialect='excel', quoting=csv.QUOTE_MINIMAL)
        for row in csvreader:
            # print row
            values += [row]
        prices.close()
        prices = values
    for row0 in prices:
        if isinstance(row, basestring):
            # FIXME: this looks hazardous, rebuilding the sequence you're iterating through
            prices = [COLUMN_SEP.split(row) for row in prices]
        break
    # print prices
    index = []
    if isinstance(prices[0][0], (datetime.date, datetime.datetime, datetime.time)):
        index = [prices[0] for row in prices]
        for i, row in prices:
            prices[i] = row[1:]
    # try to convert all strings to something numerical:
    elif any(any(isinstance(value, basestring) for value in row) for row in prices):
        #print '-'*80
        for i, row in enumerate(prices):
            #print i, row
            for j, value in enumerate(row):
                s = unicode(value).strip().strip('"').strip("'")
                #print i, j, s
                try:
                    prices[i][j] = int(s)
                    # print prices[i][j]
                except:
                    try:
                        prices[i][j] = float(s)
                    except:
                        # print 'FAIL'
                        try:
                            # this is a probably a bit too forceful
                            prices[i][j] = parse_date(s)
                        except:
                            pass
    # print prices
    width = max(len(row) for row in prices)
    datetime_width = width - num_prices
    if not index and isinstance(prices[0], (tuple, list)) and num_prices:
        # print '~'*80
        new_prices = []
        try:
            for i, row in enumerate(prices):
                # print i, row
                index += [datetime.datetime(*[int(i) for i in row[:datetime_width]])
                          + datetime.timedelta(hours=16)]
                new_prices += [row[datetime_width:]]
                # print prices[-1]
        except:
            for i, row in enumerate(prices):
                index += [row[0]]
                new_prices += [row[1:]]
        prices = new_prices or prices
    # print index
    # TODO: label the columns somehow (if first row is a bunch of strings/header)
    if len(index) == len(prices):
        df = pd.DataFrame(prices, index=index, columns=columns)
    else:
        df = pd.DataFrame(prices)
    return df
