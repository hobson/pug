from __future__ import print_function

import numpy as np
import pandas as pd


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