# util.py

from collections import Mapping

import numpy as np
from scipy import integrate
from matplotlib import pyplot as plt



def clean_dataframe(df):
    """Fill NaNs with the previous value, the next value or if all are NaN then 1.0"""
    df = df.fillna(method='ffill')
    df = df.fillna(method='bfill')
    df = df.fillna(1.0)
    return df


def make_symbols(symbols, *args):
    """Return a list of uppercase strings like "GOOG", "$SPX, "XOM"...

    Arguments:
      symbols (str or list of str): list of market ticker symbols to normalize
        If `symbols` is a str a get_symbols_from_list() call is used to retrieve the list of symbols

    Returns:
      list of str: list of cananical ticker symbol strings (typically after .upper().strip())

    Examples:
      >>> make_symbols("Goog")
      ["GOOG"]
      >>> make_symbols("  $SPX   ", " aaPL ")
      ["$SPX", "AAPL"]
      >>> make_symbols(["$SPX", ["GOOG", "AAPL"]])
      ["$SPX", "GOOG", "AAPL"]
      >>> make_symbols(" $Spy, Goog, aAPL ")
      ["$SPY", "GOOG", "AAPL"]
    """
    if (      (hasattr(symbols, '__iter__') and not any(symbols))
        or (isinstance(symbols, (list, tuple, Mapping)) and not symbols)):
        return []
    if isinstance(symbols, basestring):
        # # FIXME: find a direct API for listing all possible symbols
        # try:
        #     return list(set(dataobj.get_symbols_from_list(symbols)))
        # except:
        return [s.upper().strip() for s in symbols.split(',')]
    else:
        ans = []
        for sym in (list(symbols) + list(args)):
            tmp = make_symbols(sym)
            ans = ans + tmp
        return list(set(ans))


def integrated_change(ts, integrator=integrate.trapz, clip_floor=None, clip_ceil=float('inf')):
    """Total value * time above the starting value within a TimeSeries"""
    if clip_floor is None:
        clip_floor = ts[0]
    if clip_ceil < clip_floor:
        polarity = -1 
        offset, clip_floor, clip_ceil, = clip_ceil, clip_ceil, clip_floor
    else:
        polarity, offset = 1, clip_floor
    clipped_values = np.clip(ts.values - offset, clip_floor, clip_ceil)
    print polarity, offset, clip_floor, clip_ceil
    print clipped_values
    integrator_types = set(['trapz', 'cumtrapz', 'simps', 'romb'])
    if integrator in integrator_types:
        integrator = integrate.__getattribute__(integrator)
    integrator = integrator or integrate.trapz
    # datetime units converted to seconds (since 1/1/1970)
    return integrator(clipped_values, ts.index.astype(np.int64) / 10**9)


def clipping_start_end(ts, capacity=100):
    """Start and end index that clips the price/value of a time series the most

    Assumes that the integrated maximum includes the peak (instantaneous maximum).

    Arguments:
      ts (TimeSeries): Time series to attempt to clip to as low a max value as possible
      capacity (float): Total "funds" or "energy" available for clipping (integrated area under time series)

    Returns:
      2-tuple: Timestamp of the start and end of the period of the maximum clipped integrated increase
    """
    ts_sorted = ts.order(ascending=False)
    i, t0, t1, integral = 1, None, None, 0
    while integral <= capacity and i+1 < len(ts):
        i += 1
        t0_within_capacity = t0
        t1_within_capacity = t1
        t0 = min(ts_sorted.index[:i])
        t1 = max(ts_sorted.index[:i])
        integral = integrated_change(ts[t0:t1])
        print i, t0, ts[t0], t1, ts[t1], integral
    if t0_within_capacity and t1_within_capacity:
        return t0_within_capacity, t1_within_capacity
    # argmax = ts.argmax()  # index of the maximum value


def period_boxplot(df, period='year', column='Adj Close'):
    # df['period'] = df.groupby(lambda t: getattr(t, period)).aggregate(np.mean)
    df['period'] = getattr(df.index, period)
    perioddata = df.pivot(columns='period', values=column)
    perioddata.boxplot()
    plt.show()


