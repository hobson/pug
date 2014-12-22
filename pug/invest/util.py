# util.py
from __future__ import print_function

from collections import Mapping

import numpy as np
import pandas as pd
from scipy import integrate
from matplotlib import pyplot as plt
from matplotlib import animation

from nlp.util import listify

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
    """Insert/append threshold crossing points (time and value) into a timeseries (pd.Series)"""
    # value immediately before an upward thresh crossing
    preup = ts[(ts < thresh) & (ts.shift(-1) > thresh)]
    # values immediately after an upward thresh crossing
    postup = ts[(ts.shift(1) < thresh) & (ts > thresh)]
    # value immediately after a downward thresh crossing
    postdown = ts[(ts < thresh) & (ts.shift(1) > thresh)]
    # value immediately before an upward thresh crossing
    predown = ts[(ts.shift(-1) < thresh) & (ts > thresh)]
    # upward slope (always positive) between preup and postup in units of "value" per nanosecond (timestamps convert to floats as nanoseconds)
    slopeup = (postup.values - preup.values) / (postup.index.values - preup.index.values).astype(np.float64)
    # upward crossing point index/time
    tup = preup.index.values +  ((thresh - preup.values) / slopeup).astype(np.timedelta64)
    # downward slope (always negative) between predown and postdown in units of "value" per nanosecond (timestamps convert to floats as nanoseconds)
    slopedown = (postdown.values - predown.values) / (postdown.index.values - predown.index.values).astype(np.float64)
    # upward crossing point index/time
    tdown = predown.index.values + ((thresh - predown.values) / slopedown).astype(np.timedelta64)
    # insert crossing points into time-series (if it had a regular sample period before, it won't now!)
    ts = ts.append(pd.Series(thresh*np.ones(len(tup)), index=tup))
    # insert crossing points into time-series (if it had a regular sample period before, it won't now!)
    ts = ts.append(pd.Series(thresh*np.ones(len(tdown)), index=tdown))
    # if you don't `sort_index()`, numerical integrators in `scipy.integrate` will give the wrong answer
    return ts.sort_index()


def get_integrator(integrator):
    """Return the scipy.integrator indicated by an index, name, or integrator_function

    >>> get_integrator(0)
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
    """
    integrator = get_integrator(integrator or 0)
    ts = insert_crossings(ts, thresh) - thresh
    ts = ts[ts >= 0]
    # timestamp is in nanoseconds (since 1/1/1970) but this converts it to seconds (SI units)
    return integrator(ts, ts.index.astype(np.int64) / 1e9)


def clipping_params(ts, capacity=100):
    """Start and end index (datetime) that clips the price/value of a time series the most

    Assumes that the integrated maximum includes the peak (instantaneous maximum).

    Arguments:
      ts (TimeSeries): Time series to attempt to clip to as low a max value as possible
      capacity (float): Total "funds" or "energy" available for clipping (integrated area under time series)

    TODO:
      Return answer as a dict

    Returns:
      2-tuple: Timestamp of the start and end of the period of the maximum clipped integrated increase

    >>> t = ['2014-12-09T00:00', '2014-12-09T00:15', '2014-12-09T00:30', '2014-12-09T00:45', '2014-12-09T01:00', '2014-12-09T01:15', '2014-12-09T01:30', '2014-12-09T01:45']
    >>> import pandas as pd
    >>> ts = pd.Series([217, 234, 235, 231, 219, 219, 231, 232], index=pd.to_datetime(t))
    >>> import numpy
    >>> (clipping_params(ts, capacity=60000) ==
    ... (numpy.datetime64('2014-12-09T00:15:00.000000000+0000'),
    ... numpy.datetime64('2014-12-09T01:45:00.000000000+0000'),
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
    ts_sorted = ts.order(ascending=False)
    # default is to clip right at the peak (no clipping at all)
    i, t0, t1, integral, thresh = 1, ts_sorted.index[0], ts_sorted.index[0], 0, ts_sorted[0]
    params = {'t0': t0, 't1': t1, 'integral': 0, 'threshold': thresh}
    while integral <= capacity and i < len(ts):
        params = {'t0': pd.Timestamp(t0), 't1': pd.Timestamp(t1), 'threshold': thresh, 'integral': integral}
        i += 1
        times = ts_sorted.index[:i].values
        # print(times)
        t0 = times.min()
        t1 = times.max()
        thresh = min(ts[t0:t1])
        integral = clipped_area(ts, thresh=thresh)
    if integral <= capacity:
        return {'t0': pd.Timestamp(t0), 't1': pd.Timestamp(t1), 'threshold': thresh, 'integral': integral}
    return params


def clipping_threshold(ts, capacity=100):
    """Start and end index (datetime) that clips the price/value of a time series the most

    Assumes that the integrated maximum includes the peak (instantaneous maximum).

    Arguments:
      ts (TimeSeries): Time series to attempt to clip to as low a max value as possible
      capacity (float): Total "funds" or "energy" available for clipping (integrated area under time series)

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
    params = clipping_params(ts, capacity=capacity)
    if params:
        return params['threshold']
    return None


def period_boxplot(df, period='year', column='Adj Close'):
    # df['period'] = df.groupby(lambda t: getattr(t, period)).aggregate(np.mean)
    df['period'] = getattr(df.index, period)
    perioddata = df.pivot(columns='period', values=column)
    perioddata.boxplot()
    plt.show()


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


def animate_panel(panel, keys=None, columns=None, interval=1000, titles='', path='animate_panel', xlabel='Time', ylabel='Value', **kwargs):
    """Animate a pandas.Panel by flipping through plots of the data in each dataframe

    Arguments:
      panel (pandas.Panel): Pandas Panel of DataFrames to animate (each DataFrame is an animation video frame)
      keys (list of str): ordered list of panel keys (pages) to animate
      columns (list of str): ordered list of data series names to include in plot for eath video frame
      interval (int): number of milliseconds between video frames
      titles (str or list of str): titles to place in plot on each data frame.
        default = `keys` so that titles changes with each frame
      path (str): path and base file name to save *.mp4 animation video ('' to not save) 
      kwargs (dict): pass-through kwargs for `animation.FuncAnimation(...).save(path, **kwargs)`
        (Not used if `not path`)

    TODO: Work with other 3-D data formats:
      - dict (sorted by key) or OrderedDict
      - list of 2-D arrays/lists
      - 3-D arrays/lists
      - generators of 2-D arrays/lists
      - generators of generators of lists/arrays?

    >>> import numpy as np
    >>> import pandas as pd
    >>> x = np.arange(0, 2*np.pi, 0.05)
    >>> panel = pd.Panel(dict((i, pd.DataFrame({
    ...        'T=10': np.sin(x + i/10.),
    ...        'T=7': np.sin(x + i/7.),
    ...        'beat': np.sin(x + i/10.) + np.sin(x + i/7.),
    ...        }, index=x)
    ...    ) for i in range(50)))
    >>> ani = animate_panel(panel, interval=200, path='animate_panel_test')  # doctest: +ELLIPSIS
    <matplotlib.animation.FuncAnimation at ...>
    """

    keys = keys or list(panel.keys())
    if titles:
        titles = listify(titles)
        if len(titles) == 1:
            titles *= len(keys)
    else:
        titles = keys
    titles = dict((k, title) for k, title in zip(keys, titles))
    columns = columns or list(panel[keys[0]].columns)
    
    fig, ax = plt.subplots()

    i = 0
    df = panel[keys[i]]
    x = df.index.values
    y = df[columns].values
    lines = ax.plot(x, y)
    ax.grid('on')
    ax.title.set_text(titles[keys[0]])
    ax.xaxis.label.set_text(xlabel)
    ax.yaxis.label.set_text(ylabel)
    ax.legend(columns)

    def animate(k):
        df = panel[k]
        x = df.index.values
        y = df[columns].values.T
        ax.title.set_text(titles[k])
        for i in range(len(lines)):
            lines[i].set_xdata(x)  # all lines have to share the same x-data
            lines[i].set_ydata(y[i])  # update the data, don't replot a new line
        return lines

    # Init masks out pixels to be redrawn/cleared which speeds redrawing of plot
    def mask_lines():
        print('init')
        df = panel[0]
        x = df.index.values
        y = df[columns].values.T
        for i in range(len(lines)):
            # FIXME: why are x-values used to set the y-data coordinates of the mask?
            lines[i].set_xdata(np.ma.array(x, mask=True))
            lines[i].set_ydata(np.ma.array(y[i], mask=True))
        return lines

    ani = animation.FuncAnimation(fig, animate, keys, interval=interval, blit=False) #, init_func=mask_lines, blit=True)

    for k, v in {'writer': 'ffmpeg', 'codec': 'mpeg4', 'dpi': 100, 'bitrate': 2000}.iteritems():
        kwargs[k]=kwargs.get(k, v)
    kwargs['bitrate'] = min(kwargs['bitrate'], int(5e5 / interval))  # low information rate (long interval) might make it impossible to achieve a higher bitrate ight not
    if path and isinstance(path, basestring):
        path += + '.mp4'
        print('Saving video to {0}...'.format(path))
        ani.save(path, **kwargs)
    return ani