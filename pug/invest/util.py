# util.py
from __future__ import print_function

from collections import Mapping
import datetime

import numpy as np
import pandas as pd
from scipy import integrate

from pug.nlp.util import listify

from scipy.optimize import minimize


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

    See Also:
      pug.nlp.djdb.normalize_names

    Examples:
      >>> make_symbols("Goog")
      ["GOOG"]
      >>> sorted(make_symbols("  $SPX   ", " aaPL "))
      ["$SPX", "AAPL"]
      >>> sorted(make_symbols(["$SPX", ["GOOG", "AAPL"]]))
      ["$SPX", "AAPL", "GOOG"]
      >>> sorted(make_symbols(" $Spy, Goog, aAPL "))
      ["$SPY", "AAPL", "GOOG"]
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
    integrator = get_integrator(integrator)
    if clip_floor is None:
        clip_floor = ts[0]
    if clip_ceil < clip_floor:
        polarity = -1 
        offset, clip_floor, clip_ceil, = clip_ceil, clip_ceil, clip_floor
    else:
        polarity, offset = 1, clip_floor
    clipped_values = np.clip(ts.values - offset, clip_floor, clip_ceil)
    print(polarity, offset, clip_floor, clip_ceil)
    print(clipped_values)
    integrator_types = set(['trapz', 'cumtrapz', 'simps', 'romb'])
    if integrator in integrator_types:
        integrator = getattr(integrate, integrator)
    integrator = integrator or integrate.trapz
    # datetime units converted to seconds (since 1/1/1970)
    return integrator(clipped_values, ts.index.astype(np.int64) / 10**9)


def insert_crossings(ts, thresh):
    """Insert/append threshold crossing points (time and value) into a timeseries (pd.Series)

    Arguments:
      ts (pandas.Series): Time series of values to be interpolated at `thresh` crossings
      thresh (float or np.float64):
    """
    # import time
    # tic0 = time.clock(); tic = tic0

    # int64 for fast processing, pandas.DatetimeIndex is 5-10x slower, 0.3 ms
    index = ts.index
    index_type = type(index)
    ts.index = ts.index.astype(np.int64)
    # toc = time.clock();
    # print((toc-tic)*1000); tic = time.clock()
    
    # value immediately before an upward thresh crossing, 6 ms
    preup = ts[(ts < thresh) & (ts.shift(-1) > thresh)]
    # toc = time.clock();
    # print((toc-tic)*1000); tic = time.clock()

    # values immediately after an upward thresh crossing, 4 ms\
    postup = ts[(ts.shift(1) < thresh) & (ts > thresh)]
    # toc = time.clock();
    # print((toc-tic)*1000); tic = time.clock()

    # value immediately after a downward thresh crossing, 1.8 ms
    postdown = ts[(ts < thresh) & (ts.shift(1) > thresh)]
    # toc = time.clock();
    # print((toc-tic)*1000); tic = time.clock()

    # value immediately before an upward thresh crossing, 1.9 ms
    predown = ts[(ts.shift(-1) < thresh) & (ts > thresh)]
    # toc = time.clock();
    # print((toc-tic)*1000); tic = time.clock()

    # upward slope (always positive) between preup and postup in units of "value" per nanosecond (timestamps convert to floats as nanoseconds), 0.04 ms
    slopeup = (postup.values - preup.values) / (postup.index.values - preup.index.values).astype(np.float64)
    # toc = time.clock();
    # print((toc-tic)*1000); tic = time.clock()

    # upward crossing point index/time, 0.04 ms
    tup = preup.index.values +  ((thresh - preup.values) / slopeup).astype(np.int64)
    # toc = time.clock();
    # print((toc-tic)*1000); tic = time.clock()

    # downward slope (always negative) between predown and postdown in units of "value" per nanosecond (timestamps convert to floats as nanoseconds), 0.03 ms
    slopedown = (postdown.values - predown.values) / (postdown.index.values - predown.index.values).astype(np.float64)
    # toc = time.clock();
    # print((toc-tic)*1000); tic = time.clock()

    # upward crossing point index/time, 0.02 ms
    tdown = predown.index.values + ((thresh - predown.values) / slopedown).astype(np.int64)
    # toc = time.clock();
    # print((toc-tic)*1000); tic = time.clock()

    # insert crossing points into time-series (if it had a regular sample period before, it won't now!), 2.0 ms
    ts.index = index  # pd.DatetimeIndex(ts.index)
    # toc = time.clock();
    # print((toc-tic)*1000); tic = time.clock()

    # insert crossing points into time-series (if it had a regular sample period before, it won't now!), 2.0 ms
    ts = ts.append(pd.Series(thresh*np.ones(len(tup)), index=index_type(tup.astype(np.int64))))
    # toc = time.clock();
    # print((toc-tic)*1000); tic = time.clock()

    # insert crossing points into time-series (if it had a regular sample period before, it won't now!), 1.9 ms
    ts = ts.append(pd.Series(thresh*np.ones(len(tdown)), index=index_type(tdown.astype(np.int64))))
    # toc = time.clock();
    # print((toc-tic)*1000); tic = time.clock()

    # if you don't `sort_index()`, numerical integrators in `scipy.integrate` will give the wrong answer, 0.1 ms
    ts = ts.sort_index()
    # toc = time.clock();
    # print((toc-tic)*1000); tic = time.clock()    # if you don't `sort_index()`, numerical integrators in `scipy.integrate` will give the wrong answer

    # print((toc-tic0)*1000); 
    return ts

def get_integrator(integrator):
    """Return the scipy.integrator indicated by an index, name, or integrator_function

    >> get_integrator(0)
    """
    integrator_types = set(['trapz', 'cumtrapz', 'simps', 'romb'])
    integrator_funcs = [integrate.trapz, integrate.cumtrapz, integrate.simps, integrate.romb]

    if isinstance(integrator, int) and 0 <= integrator < len(integrator_types):
        integrator = integrator_types[integrator]
    if isinstance(integrator, basestring) and integrator in integrator_types:
        return getattr(integrate, integrator)
    elif integrator in integrator_funcs:
        return integrator
    else:
        print('Unsupported integration rule: {0}'.format(integrator))
        print('Expecting one of these sample-based integration rules: %s' % (str(list(integrator_types))))
        raise AttributeError
    return integrator


def clipped_area(ts, thresh=0, integrator=integrate.trapz):
    """Total value * time above the starting value within a TimeSeries

    Arguments:
      ts (pandas.Series): Time series to be integrated.
      thresh (float): Value to clip the tops off at (crossings will be interpolated)

    References:
      http://nbviewer.ipython.org/gist/kermit666/5720498

    >>> t = ['2014-12-09T00:00', '2014-12-09T00:15', '2014-12-09T00:30', '2014-12-09T00:45', '2014-12-09T01:00', '2014-12-09T01:15', '2014-12-09T01:30', '2014-12-09T01:45']
    >>> import pandas as pd
    >>> ts = pd.Series([217, 234, 235, 231, 219, 219, 231, 232], index=pd.to_datetime(t))
    >>> clipped_area(ts, thresh=230)  # doctest: +ELLIPSIS
    8598.52941...
    >>> clipped_area(ts, thresh=234)  # doctest: +ELLIPSIS
    562.5
    >>> clipped_area(pd.Series(ts.values, index=ts.index.values.astype(pd.np.int64)), thresh=234)  # doctest: +ELLIPSIS
    562.5    
    """
    integrator = get_integrator(integrator or 0)
    ts = insert_crossings(ts, thresh) - thresh
    ts = ts[ts >= 0]
    # timestamp is in nanoseconds (since 1/1/1970) but this converts it to seconds (SI units)
    return integrator(ts, ts.index.astype(np.int64))  / 1.0e9


def clipping_params(ts, capacity=100, rate_limit=float('inf')):
    """Start, end, and threshold that clips the value of a time series the most, given a limitted "capacity" and "rate"

    Assumes that signal can be linearly interpolated between points (trapezoidal integration)

    Arguments:
      ts (TimeSeries): Time series to attempt to clip to as low a max value as possible
      capacity (float): Total "funds" or "energy" available for clipping (integrated area under time series)

    TODO:
      Bisection search for the optimal threshold.

    Returns:
      2-tuple: Timestamp of the start and end of the period of the maximum clipped integrated increase

    >>> t = ['2014-12-09T00:00', '2014-12-09T00:15', '2014-12-09T00:30', '2014-12-09T00:45', '2014-12-09T01:00', '2014-12-09T01:15', '2014-12-09T01:30', '2014-12-09T01:45']
    >>> import pandas as pd
    >>> ts = pd.Series([217, 234, 235, 231, 219, 219, 231, 232], index=pd.to_datetime(t))
    >>> import numpy
    >>> (clipping_params(ts, capacity=60000) ==
    ... 54555.882353782654,
    ... 219))
    True
    >>> (clipping_params(ts, capacity=30000) ==
    ... (numpy.datetime64('2014-12-09T00:15:00.000000000+0000'),
    ... numpy.datetime64('2014-12-09T00:30:00.000000000+0000'),
    ... 562.5,
    ... 234))
    True
    """
    #index_type = ts.index.dtype
    #ts2 = ts.copy()
    ts.index = ts.index.astype(np.int64)
    costs = []

    def cost_fun(x, *args):
        thresh = x[0]
        ts, capacity, bounds = args
        integral = clipped_area(ts, thresh=thresh)
        terms = np.array([(10. * (integral - capacity) / capacity) ** 2,
                        2. / 0.1**((bounds[0] - thresh) * capacity / bounds[0]),
                        2. / 0.1**((thresh - bounds[1]) * capacity / bounds[1]),
                        1.2 ** (integral / capacity)])
        return sum(terms)

    bounds = (ts.min(), ts.max())
    thresh0 = 0.9*bounds[1] + 0.1*bounds[0]
    optimum = minimize(fun=cost_fun, x0=[thresh0], bounds=[bounds], args=(ts, capacity, bounds))
    thresh = optimum.x[0]
    integral = clipped_area(ts, thresh=thresh)
    return {'costs': costs, 'optimize_result': optimum, 'threshold': thresh, 'integral': integral}
    # if integral - capacity > capacity:
    #     return {'t0': None, 't1': None, 'threshold': 0.96*thresh + 0.06*bounds[0][1], 'integral': integral}


def discrete_clipping_params(ts, capacity=100, rate_limit=float('inf')):
    """Start, end, and threshold that clips the value of a time series the most, given a limitted "capacity" and "rate"

    Assumes that the integrated maximum includes the peak (instantaneous maximum).
    Assumes that the threshold can only set to one of the values of the Series.

    Arguments:
      ts (TimeSeries): Time series to attempt to clip to as low a max value as possible
      capacity (float): Total "funds" or "energy" available for clipping (integrated area under time series)

    TODO:
      Bisection search for the optimal threshold.

    Returns:
      2-tuple: Timestamp of the start and end of the period of the maximum clipped integrated increase

    >>> t = ['2014-12-09T00:00', '2014-12-09T00:15', '2014-12-09T00:30', '2014-12-09T00:45', '2014-12-09T01:00', '2014-12-09T01:15', '2014-12-09T01:30', '2014-12-09T01:45']
    >>> import pandas as pd
    >>> ts = pd.Series([217, 234, 235, 231, 219, 219, 231, 232], index=pd.to_datetime(t))
    >>> import numpy
    >>> (discrete_clipping_params(ts, capacity=60000) ==
    ... (numpy.datetime64('2014-12-09T00:15:00.000000000+0000'),
    ... numpy.datetime64('2014-12-09T01:45:00.000000000+0000'),
    ... 54555.882353782654,
    ... 219))
    True
    >>> (discrete_clipping_params(ts, capacity=30000) ==
    ... (numpy.datetime64('2014-12-09T00:15:00.000000000+0000'),
    ... numpy.datetime64('2014-12-09T00:30:00.000000000+0000'),
    ... 562.5,
    ... 234))
    True
    """
    #index_type = ts.index.dtype
    #ts2 = ts.copy()
    ts.index = ts.index.astype(np.int64)
    ts_sorted = ts.order(ascending=False)
    # default is to clip right at the peak (no clipping at all)
    i, t0, t1, integral, thresh = 1, ts_sorted.index[0], ts_sorted.index[0], 0, ts_sorted.iloc[0]
    params = {'t0': t0, 't1': t1, 'integral': 0, 'threshold': thresh}
    while i < len(ts_sorted) and integral <= capacity and (ts_sorted.iloc[0] - ts_sorted.iloc[i]) < rate_limit:
        params = {'t0': pd.Timestamp(t0), 't1': pd.Timestamp(t1), 'threshold': thresh, 'integral': integral}
        i += 1
        times = ts_sorted.index[:i]
        # print(times)
        t0 = times.min()
        t1 = times.max()
        # print(ts_sorted.index[:3])
        thresh = min(ts_sorted.iloc[:i])
        integral = clipped_area(ts, thresh=thresh)
    if integral <= capacity:
        return {'t0': pd.Timestamp(t0), 't1': pd.Timestamp(t1), 'threshold': thresh, 'integral': integral}
    return params


def square_off(series, time_delta=None, transition_seconds=1):
    """Insert samples in regularly sampled data to produce stairsteps from ramps when plotted.

    New samples are 1 second (1e9 ns) before each existing samples, to facilitate plotting and sorting

    >>> square_off(pd.Series(range(3), index=pd.date_range('2014-01-01', periods=3, freq='15m')), time_delta=5.5)  # doctest: +NORMALIZE_WHITESPACE
    2014-01-31 00:00:00           0
    2014-01-31 00:00:05.500000    0
    2015-04-30 00:00:00           1
    2015-04-30 00:00:05.500000    1
    2016-07-31 00:00:00           2
    2016-07-31 00:00:05.500000    2
    dtype: int64
    >>> square_off(pd.Series(range(2), index=pd.date_range('2014-01-01', periods=2, freq='15min')), transition_seconds=2.5)  # doctest: +NORMALIZE_WHITESPACE
    2012-01-01 00:00:00           0
    2012-01-01 00:14:57.500000    0
    2012-01-01 00:15:00           1
    2012-01-01 00:29:57.500000    1
    dtype: int64
    """
    if time_delta:
        # int, float means delta is in seconds (not years!)
        if isinstance(time_delta, (int, float)):
            time_delta = datetime.timedelta(0, time_delta)
        new_times = series.index + time_delta
    else:
        diff = np.diff(series.index)
        time_delta = np.append(diff, [diff[-1]])
        new_times = series.index + time_delta
        new_times = pd.DatetimeIndex(new_times) - datetime.timedelta(0, transition_seconds)
    return pd.concat([series, pd.Series(series.values, index=new_times)]).sort_index()


def clipping_threshold(ts, capacity=100, rate_limit=10):
    """Start and end index (datetime) that clips the price/value of a time series the most

    Assumes that the integrated maximum includes the peak (instantaneous maximum).

    Arguments:
      ts (TimeSeries): Time series of prices or power readings to be "clipped" as much as possible.
      capacity (float): Total "funds" or "energy" available for clipping (in $ or Joules)
        The maximum allowed integrated area under time series and above the clipping threshold.
      rate_limit: Maximum rate at which funds or energy can be expended (in $/s or Watts)
        The clipping threshold is limitted to no less than the peak power (price rate) minus this rate_limit

    TODO:
      Return answer as a dict

    Returns:
      2-tuple: Timestamp of the start and end of the period of the maximum clipped integrated increase

    >>> t = ['2014-12-09T00:00', '2014-12-09T00:15', '2014-12-09T00:30', '2014-12-09T00:45', '2014-12-09T01:00', '2014-12-09T01:15', '2014-12-09T01:30', '2014-12-09T01:45']
    >>> import pandas as pd
    >>> ts = pd.Series([217, 234, 235, 231, 219, 219, 231, 232], index=pd.to_datetime(t))
    >>> clipping_threshold(ts, capacity=60000)
    219
    >>> clipping_threshold(ts, capacity=30000)
    234
    """
    params = discrete_clipping_params(ts, capacity=capacity, rate_limit=rate_limit)
    if params:
        return params['threshold']
    return None



def join_time_series(serieses, ignore_year=False, T_s=None, aggregator='mean'):
    """Combine a dict of pd.Series objects into a single pd.DataFrame with optional downsampling

    FIXME:
      For ignore_year and multi-year data, the index (in seconds) is computed assuming
      366 days per year (leap year). So 3 out of 4 years will have a 1-day (86400 s) gap

    Arguments:
      series (dict of Series): dictionary of named timestamp-indexed Series objects
      ignore_year (bool): ignore the calendar year, but not the season (day of year)
         If True, the DataFrame index will be seconds since the beginning of the 
         year in each Series index, i.e. midnight Jan 1, 2014 will have index=0 
         as will Jan 1, 2010 if two Series start on those two dates.
      T_s (float): sample period in seconds (for downsampling)
      aggregator (str or func): e.g. 'mean', 'sum', np.std
    """
    if ignore_year:
        df = pd.DataFrame()
        for name, ts in serieses.iteritems():
            # FIXME: deal with leap years
            sod = np.array(map(lambda x: (x.hour*3600 + x.minute*60 + x.second),
                                       ts.index.time))
            # important that soy is an integer so that merge/join operations identify same values (floats don't equal!?)
            soy = (ts.index.dayofyear + 366*(ts.index.year - ts.index.year[0])) * 3600 * 24 + sod
            ts2 = pd.Series(ts.values, index=soy)
            ts2 = ts2.dropna()
            ts2 = ts2.sort_index()
            df2 = pd.DataFrame({name: ts2.values}, index=soy)

            df = df.join(df2, how='outer')
        if T_s and aggregator:
            df = df.groupby(lambda x: int(x/float(T_s))).aggregate(dict((name, aggregator) for name in df.columns))
    else:
        df = pd.DataFrame(serieses)
        if T_s and aggregator:
            x0 = df.index[0]
            df = df.groupby(lambda x: int((x-x0).total_seconds()/float(T_s))).aggregate(dict((name, aggregator) for name in df.columns))
            # FIXME: convert seconds since begninning of first year back into Timestamp instances
    return df


def simulate(t=1000, poly=(0.,), sinusoids=None, sigma=0, rw=0, irw=0, rrw=0):
    """Simulate a random signal with seasonal (sinusoids), linear and quadratic trend, RW, IRW, and RRW

    Arguments:
      t (int or list of float): number of samples or time vector, default = 1000
      poly (list of float): polynomial coefficients (in decreasing "order") passed to `numpy.polyval`
         i.e. poly[0]*x**(N-1) + ... + poly[N-1]
      sinusoids (list of list): [[period], [amplitude, period], or [ampl., period, phase]]

    >>> len(simulate(poly=(0,),rrw=1))
    1000
    >>> simulate(t=range(3), poly=(1,2))  # doctest: +NORMALIZE_WHITESPACE
    0    2
    1    3
    2    4
    dtype: float64
    >>> all(simulate(t=50, sinusoids=((1,2,3),)) == simulate(t=range(50), sinusoids=((1,2,3),)))
    True   
    >>> any(simulate(t=100))
    False
    >>> abs(simulate(sinusoids=42.42).values[1] + simulate(sinusoids=42.42).values[-1]) < 1e-10
    True
    >>> simulate(t=17,sinusoids=[42, 16]).min()
    -42.0
    >>> all((simulate(t=range(10), sinusoids=(1, 9, 4.5))+simulate(t=10, sinusoids=(1,9))).abs() < 1e-10)
    True
    """
    if t and isinstance(t, int):
        t = np.arange(t, dtype=np.float64)
    else:
        t = np.array(t, dtype=np.float64)
    N = len(t)
    poly = poly or (0.,)
    poly = listify(poly)
    y = np.polyval(poly, t)
    sinusoids = listify(sinusoids or [])
    if any(isinstance(ATP, (int, float)) for ATP in sinusoids):
        sinusoids = [sinusoids]
    for ATP in sinusoids:
        # default period is 1 more than the length of the simulated series (no values of the cycle are repeated)
        T = (t[-1] - t[0]) * N / (N - 1.)
        # default amplitude is 1 and phase is 0
        A, P = 1., 0
        try:
            A, T, P = ATP
        except (TypeError, ValueError):
            try:
                A, T = ATP
            except (TypeError, ValueError):
                # default period is 1 more than the length of the simulated series (no values of the cycle are repeated)
                A = ATP[0]
        # print(A, T, P)
        # print(t[1] - t[0])
        y += A * np.sin(2 * np.pi * (t - P) / T)
    if sigma:
        y += np.random.normal(0.0, float(sigma), N)
    if rw:
        y += np.random.normal(0.0, float(rw), N).cumsum()
    if irw:
        y += np.random.normal(0.0, float(irw), N).cumsum().cumsum()
    if rrw:
        y += np.random.normal(0.0, float(rrw), N).cumsum().cumsum().cumsum()
    return pd.Series(y, index=t)


