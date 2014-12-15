from __future__ import print_function

import datetime

import concurrentpandas as ccp

from django.db import models
from jsonfield import JSONField

from invest import util
import nlp

import pandas as pd


class Equity(models.Model):
    name = models.CharField(help_text='Full legal name of busienss or fund.', 
        max_length=64, null=False, blank=False)
    symbol = models.CharField(max_length=10, null=False, blank=False)
    time_series = JSONField()


class Day(models.Model):
    """Daily time series Data"""
    day = models.IntegerField(help_text="Trading days since Jan 1, 1970", null=True, blank=True)
    close = models.FloatField(null=True, default=None)
    actual_close = models.FloatField(null=True, default=None, blank=True)
    volume = models.FloatField(null=True, default=None, blank=True)
    date = models.DateField(null=False)
    datetime = models.DateTimeField(null=False)
    high = models.FloatField(null=True, default=None, blank=True)
    low = models.FloatField(null=True, default=None, blank=True)
    symbol = models.CharField(max_length=10, null=False, blank=False)
    equity = models.ForeignKey(Equity)


def get_dataframes(symbols=("sne", "goog", "tsla"), source='yahoo', refresh=False):
    """Retreive table of market data ("Close", "Volume", "Adj Close") for each symbol requested

    >>> dfdict = get_dataframes('GOOG', 'SNE')
    """
    symbols = util.make_symbols(list(symbols))
    if refresh:
        symbols_to_refresh = symbols
    else:
        symbols_to_refresh = [sym for sym in symbols if not Equity.objects.filter(symbol=sym).exists()]
    source = source.lower().strip()
    if source in ('yahoo', 'google'):
        source += '_finance'
    if source[:3] == 'fed':
        source = 'federal_reserve_economic_data'
    ccpanda = ccp.ConcurrentPandas()
    # set the data source
    getattr(ccpanda, "set_source_" + source)()
    if symbols_to_refresh:
        # tell concurrent pandas which keys/symbols to retrieve
        ccpanda.insert_keys(symbols_to_refresh)
        # start concurrentpandas threads
        ccpanda.consume_keys_asynchronous_threads()
        # FIXME: is there a better/faster iterator to use like `ccpanda.output_map` attribute?
        pseudodict = ccpanda.return_map()
    else:
        pseudodict = {}
    table = {}
    for sym in symbols:
        e, created = None, False
        if not sym in symbols_to_refresh:
            e, created = Equity.objects.get_or_create(symbol=sym)
        if created or not e or not e.time_series or sym in symbols_to_refresh:
            e, created = Equity.objects.get_or_create(
                symbol=sym,
                name=sym,  # FIXME: use data source to find equity name!
                time_series=pseudodict[sym].to_json(),
                )
        table[sym] = pd.io.json.read_json(path_or_buf=e.time_series, orient='columns', typ='frame', convert_dates=True)
    return table


def get_panel(*args, **kwargs):
    return pd.Panel(get_dataframes(*args, **kwargs))


def price_dataframe(symbols=('sne',),
    start=datetime.datetime(2008, 1, 1),
    end=datetime.datetime(2009, 12, 31),
    price_type='actual_close',
    cleaner=util.clean_dataframe,
    ):
    """Retrieve the prices of a list of equities as a DataFrame (columns = symbols)

    Arguments:
      symbols (list of str): Ticker symbols like "GOOG", "AAPL", etc
        e.g. ["AAPL", " slv ", GLD", "GOOG", "$SPX", "XOM", "msft"]
      start (datetime): The date at the start of the period being analyzed.
      end (datetime): The date at the end of the period being analyzed.
        Yahoo data stops at 2013/1/1
    """
    if isinstance(price_type, basestring):
        price_type = [price_type]
    start = nlp.util.normalize_date(start or datetime.date(2008, 1, 1))
    end = nlp.util.normalize_date(end or datetime.date(2009, 12, 31))
    symbols = util.make_symbols(symbols)
    df = get_dataframes(symbols)
    # t = du.getNYSEdays(start, end, datetime.timedelta(hours=16))
    # df = clean_dataframes(dataobj.get_data(t, symbols, price_type))
    if not df or len(df) > 1:
        return cleaner(df)
    else:
        return cleaner(df[0])

