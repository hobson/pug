#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Abtstraction of an abstraction (the Django Database ORM)

Makes data processing easier:

    * numerical processing with `numpy`
    * text processing with `nltk` and `pub.nlp`
    * visualization with d3, nvd3, and django-nvd3
    * data structure manipulations (listify, intify)
"""

import datetime
import calendar
from math import log
import json
import chardet
import re

import pytz
from dateutil import parser as dateutil_parser
import logging

logger = logging.getLogger('bigdata.info')

from pug.nlp import util  # import transposed_lists, sod_transposed, listify, intify
from pug.nlp import regex_patterns

NULL_VALUES = (None, 'None', 'none', '<None>', 'NONE', 'Null', 'null', '<Null>', 'N/A', 'n/a', 'NULL')
NAN_VALUES = (float('inf'), 'INF', 'inf', '+inf', '+INF', float('nan'), 'nan', 'NAN', float('-inf'), '-INF', '-inf')
BLANK_VALUES = ('', ' ', '\t', '\n', '\r', ',')

FALSE_VALUES = (False, 'False', 'false', 'FALSE', 'F')
TRUE_VALUES = (True, 'True', 'true', 'TRUE', 'T')

NO_VALUES = ('No', 'no', 'N')
YES_VALUES = ('Yes', 'yes', 'Y')

from django.db.models.base import ModelBase


class RobustEncoder(json.JSONEncoder):
    """A more robust JSON serializer (handles any object with a __str__ method).

    from http://stackoverflow.com/a/15823348/623735
    Fixes: "TypeError: datetime.datetime(..., tzinfo=<UTC>) is not JSON serializable"

    >>> import datetime
    >>> json.dumps(datetime.datetime(1,2,3), cls=RobustEncoder)
    '"0001-02-03 00:00:00"'
    """
    def default(self, obj):
        # if isinstance(obj, (datetime.datetime, Decimal)):
        #     obj = str(obj)
        if isinstance(obj, (list, dict, tuple, int, float, basestring, bool, type(None))):
            return super(RobustEncoder, self).default(obj)
        if isinstance(obj, ModelBase):
            return str(getattr(obj, 'pk', '') or None)
        return str(obj)


def has_suffix(model, suffixes=('Orig',)):
    for suffix in suffixes:
        if model._meta.object_name.endswith(suffix) or model._meta.db_table.endswith(suffix):
            return True
    return False


def has_prefix(model, prefixes=('Wiki')):
    for prefix in prefixes:
        if model._meta.object_name.startswith(prefix) or model._meta.db_table.startswith(prefix):
            return True
    return False


def representation(model, field_names=None):
    """
    Unicode representation of a particular model instance (object or record or DB table row)

    TODO:
    - check for _meta.unique_together and use them to order the all_names list
    - do fuzzywuzzy matching on field names to identify important fields automatically (name, id, serial, model, account, last, first, email, phone, city)
    """
    if field_names is None:
        all_names = model._meta.get_all_field_names()
        field_names = None
        for field_names_name in ('IMPORTANT_FIELDS', '_IMPORTANT_FIELDS', '_important_fields', 'REPR_FIELDS', '_REPR_FIELDS', '_repr_fields'):  #, 'SECURE_FIELDS', '_secure_fields'):
            field_names = getattr(model, field_names_name, None)  # or getattr(getattr(model, '_meta', None), field_names_name, None) # ticket 5793 wont fix, custom Meta.* not allowed 
            if field_names:
                break
    field_names = field_names or (['pk'] + all_names[:min(representation.default_fields, len(all_names))])
    return (model.__class__.__name__
        + '('
        + ', '.join("%s" % (repr(getattr(model, s, '') or '')) for s in field_names[:min(len(field_names), representation.max_fields)])
        + ')')
representation.max_fields = 10
representation.default_fields = 3


def _link_rels(model, fields=None, save=False, overwrite=False):
    """Excercise all the hidden relationship-linking methods of the self model instance"""
    if fields is None:  # allow an empty tuple for the case where you don't want to search for any hidden link_rel functions
        fields = model._meta.get_all_field_names()
    # TODO: filter out all fields that aren't fields of type `Related`
    #       Except that this would ignore fields like case_number Integer that needs to be populated using _case_number just like the case_master FK
    for field in fields:
        if not overwrite and getattr(model, field.lower(), None):
            continue
        if hasattr(model, field):
            setattr(model, field, getattr(model, '_' + field, None))
    if save:
        model.save()


def best_scale_factor(x, y):
    """Maximum distance from zero for one variable relative to another

    >>> best_scale_factor([.1, .2, .3], [.2, .4, .6])  # doctest: +ELLIPSIS
    2.0
    >>> best_scale_factor([-.1, -.2, -.3], [-1, -2, -3])  # doctest: +ELLIPSIS
    10.0

    For speed and simplicity, the scale factor is intended for data near or crossing zero.
    It is not the maximum relative ranges of the data.
    """
    if any(x) and any(y):
        return float(max(abs(min(y)), abs(max(y)))) / max(abs(min(x)), abs(max(x)))
    return 1.


def round_to_place(x, decimal_place=-1):
    """
    >>> round_to_place(12345.6789, -3)  # doctest: +ELLIPSIS
    12000.0
    >>> round_to_place(12345, -2)  # doctest: +ELLIPSIS
    12300
    >>> round_to_place(12345.6789, 2)  # doctest: +ELLIPSIS
    12345.68
    """
    t = type(x)
    return t(round(float(x), decimal_place))


def round_to_sigfigs(x, sigfigs=1):
    """
    >>> round_to_sigfigs(12345.6789, 7)  # doctest: +ELLIPSIS
    12345.68
    >>> round_to_sigfigs(12345.6789, 1)  # doctest: +ELLIPSIS
    10000.0
    >>> round_to_sigfigs(12345.6789, 0)  # doctest: +ELLIPSIS
    100000.0
    >>> round_to_sigfigs(12345.6789, -1)  # doctest: +ELLIPSIS
    1000000.0
    """
    place = int(log(x, 10))
    if sigfigs <= 0:
        additional_place = x > 10. ** place
        return 10. ** (     -sigfigs + place + additional_place)
    return round_to_place(x, sigfigs - 1 - place)


def sorted_dict_of_lists(dict_of_lists, field_names, reverse=False):
    """Sort a list of lists as if each list is a column (not a row as builtin sorted does) excel does, in the order listed in field names

    >>> sorted(sorted_dict_of_lists({'k1': [1, 2, 3], 'k2': [7, 8, 6], 'k3': [6, 5, 4]}, field_names=['k2', 'k1', 'k3']).items())
    [('k1', [3, 1, 2]), ('k2', [6, 7, 8]), ('k3', [4, 6, 5])]
    >>> sorted(sorted_dict_of_lists({'k1': [1, 2, 3], 'k2': [7, 8, 6], 'k3': [6, 5, 4]}, field_names=['k2', 'k1', 'k3'], reverse=True).items())
    [('k1', [2, 1, 3]), ('k2', [8, 7, 6]), ('k3', [5, 6, 4])]
    """
    lists = [dict_of_lists[k] for k in field_names]
    # FIXME: won't this unsort it, since the return value isn't an OrderedDict ?
    return dict(zip(field_names, util.transposed_lists(sorted(util.transposed_lists(lists), reverse=reverse))))


def consolidated_counts(dict_of_lists, field_name, count_name='count'):
    accumulated_counts = {}
    for i, db_value in enumerate(dict_of_lists[field_name]):
        if not accumulated_counts.get(db_value):
            accumulated_counts[db_value] = 0
        accumulated_counts[db_value] += dict_of_lists[count_name][i]

    dict_of_lists[field_name] = []
    dict_of_lists[count_name] = []
    
    for k in accumulated_counts:
        dict_of_lists[field_name] += [k]
        dict_of_lists[count_name] += [accumulated_counts[k]]
    return dict_of_lists


def sort_prefix(sort):
    if sort in ('-1', -1, -1., '-'):
        return '-'
    elif sort in ('+1', +1, +1., '+', True):
        return ''



def epoch_in_milliseconds(epoch):
    """
    >>> epoch_in_milliseconds(datetime_from_seconds(-12345678999.0001))
    -12345679000000
    """
    return epoch_in_seconds(epoch) * 1000

# Unix is Jan 1, 1970: datetime.datetime(1970, 1, 1, 0, 0)
DEFAULT_DATETIME_EPOCH = datetime.datetime.fromtimestamp(0, pytz.utc)

def epoch_in_seconds(epoch):
    """
    >>> epoch_in_seconds(datetime_from_seconds(-12345678999.0001))
    -12345679000
    """
    if epoch == 0:
        # if you specifiy zero year, assume you meant AD 0001 (Anno Domini, Christ's birth date?) 
        epoch = datetime.datetime(1, 1, 1)
    try:
        epoch = int(epoch)
    except:
        try:
            epoch = float(epoch)
        except:
            pass
    # None will use the default epoch (1970 on Unix)
    epoch = epoch or DEFAULT_DATETIME_EPOCH
    if epoch:
        try:
            return calendar.timegm(epoch.timetuple())
        except:
            try:
                return calendar.timegm(datetime.date(epoch,1,1).timetuple())
            except:  # TypeError on non-int epoch
                try:
                    epoch = float(epoch)
                    assert(abs(int(float(epoch))) <= 5000)
                    return calendar.timegm(datetime.date(int(epoch),1,1).timetuple())
                except:
                    pass
    return epoch


def epoch_as_datetime(epoch=None, tz=pytz.UTC):
    """
    >>> datetime_in_seconds(epoch_as_datetime())
    0.0
    """
    if epoch == 0.:
        return datetime.datetime(1, 1, 1)
    # None will use the default epoch (1970 on Unix)
    epoch = epoch or DEFAULT_DATETIME_EPOCH
    if isinstance(epoch, (datetime.datetime, datetime.date, datetime.timedelta)):
        return epoch
    if isinstance(epoch, (int, long)) and abs(int(float(epoch))) <= 5000:
        return datetime.date(int(epoch),1,1)
    try:
        return datetime.datetime.fromtimestamp(calendar.timegm(epoch), tz)
    except:
        try:
            return datetime.datetime.fromtimestamp(epoch, tz)
        except:
            pass
    return epoch


# None will use the default epoch (1970 on Unix)
def datetime_in_milliseconds(x, epoch=None):
    """
    Number of milliseconds since 1970 (UNIX timestamp), floored (truncated) to 1 second precision.

    >>> datetime_in_milliseconds(datetime_from_seconds(123))
    123000.0
    >>> datetime_in_milliseconds(datetime.date(1970,1,1))
    0.0
    >>> datetime_in_milliseconds(datetime.date(1970,1,2))
    86400000.0
    >>> datetime_in_milliseconds(datetime.datetime(1970, 1, 2, 0, 0, 1))
    86401000.0
    >>> datetime_in_milliseconds([datetime.datetime(2030, 12, 31, 0, 0, 1), datetime.datetime(2030, 12, 31)])
    [1924905601000.0, 1924905600000.0]
    """
    if epoch:
        try:
            epoch_in_seconds = float(epoch) / 1000.
        except:
            epoch_in_seconds = datetime_in_seconds(x=epoch, epoch=0)
    else:
        epoch = 0
    try:
        result = datetime_in_seconds(x, epoch=epoch_in_seconds)
    except:
        result = x
    if not isinstance(x, (datetime.datetime, datetime.date, datetime.timedelta)):
        try:
            return type(x)([t * 1000 for t in result])
        except:
            pass
    return result * 1000
unix_timestamp = datetime_in_milliseconds


def datetime_in_seconds(x, epoch=None):
    """
    Number of seconds since 1970, floored (truncated) to 1 second precision.

    >>> datetime_in_seconds(datetime_from_seconds(123456789123))
    123456789123.0
    >>> datetime_in_seconds([datetime.datetime(2010, 10, 31, 0, 0, 1), datetime.datetime(2010, 10, 31)])
    [1288483201.0, 1288483200.0]
    """
    if epoch:
        epoch = datetime_in_seconds(x=epoch, epoch=0)
    else:
        epoch = 0
    try:
        return float(x) - epoch
    except:
        pass
    if hasattr(x, 'timetuple'):
        return datetime_in_seconds(calendar.timegm(x.timetuple()), epoch=epoch)
    if isinstance(x, basestring):
        return datetime_in_seconds(dateutil_parser.parse(x), epoch=epoch)
    if isinstance(x, (list, tuple)):
        return type(x)([datetime_in_seconds(dt, epoch=epoch) for dt in x])
#     if isinstance(x, datetime.datetime):
#         return (x - epoch_as_datetime(epoch)).total_seconds()
#     if hasattr(x, 'timetuple'):
#         return datetime_in_seconds(calendar.timegm(x.timetuple()), epoch=epoch)
#     if isinstance(x, float):
#         return long(x) - epoch_in_seconds(epoch)
#     if isinstance(x, (int, long)):
#         return x - epoch_in_seconds(epoch)
#     if isinstance(x, basestring):
#         return datetime_in_seconds(dateutil_parser.parse(x), epoch=epoch)
#     if isinstance(x, (list, tuple)):
#         return type(x)([datetime_in_seconds(dt, epoch=epoch) for dt in x])


def to_ordinal(date):
    """
    >>> to_ordinal(datetime.datetime(1777, 11, 15, 23, 59, 59, 999999))
    648990
    >>> to_ordinal(datetime.date(1, 1, 2))
    2
    """
    try:
        return date.toordinal()
    except:
        # don't waste time with the parser, unless it's a string, and raise an exception if it's a string that doesn't convert to a date or an integer
        if isinstance(date, basestring):
            try:
                return dateutil_parser.parse(date)
            except:
                return int(float(date))
    # "vectorize" the datetime.toordinal method
    return type(date)(to_ordinal(d) for d in date)


def to_date(ordinal):
    """
    >>> to_date(1)
    datetime.date(1, 1, 1)
    >>> to_date(to_ordinal([datetime.date(1776, 7, 4), datetime.datetime(1777, 11, 15, 23, 59, 59, 999999)]))
    [datetime.date(1776, 7, 4), datetime.date(1777, 11, 15)]
    >>> to_date(to_ordinal((datetime.date(1776, 7, 4), datetime.datetime(2013, 11, 8, 3, 4))))
    (datetime.date(1776, 7, 4), datetime.date(2013, 11, 8))
    >>> to_date((1492, 12, 25))
    datetime.date(1492, 12, 25)
    """
    try:
        return datetime.date.fromordinal(ordinal)
    except:
        # don't waste time with the parser, unless it's a string, and raise an exception if it's a string that doesn't convert to a date or an integer
        if isinstance(ordinal, basestring):
            try:
                return datetime.date.fromordinal(int(float(ordinal)))
            except:
                return dateutil_parser.parse(ordinal)
        # need to make sure it's a 3-tuple iterable before converting it, because it might be a tuple of orindals
        # TODO: store a list of bounds on acceptable dates to check before attempting conversion (e.g. 1-3000, 1-12, 1-31) 
        elif hasattr(ordinal, '__iter__') and len(tuple(ordinal)) == 3 and all((isinstance(o, int) and 10000 > o > 0) for o in ordinal):
            # don't try/except so that exception is raised if assumption that this was a date tuple (instead of ordinal tuple) were incorrect
            return datetime.date(*tuple(ordinal))
    return type(ordinal)(to_date(o) for o in ordinal)


def datetime_from_seconds(x, tz=pytz.utc):
    if isinstance(x, datetime.datetime):
        return x
    if isinstance(x, (list, tuple)):
        return type(x)([datetime_from_seconds(dt) for dt in x])
    return datetime.datetime.fromtimestamp(x, tz)



def guess_epochs(dt1, dt2):
    """
    TODO: Be more clever and return epochs for both dates instead of just one, and allow searching of vectors
    """
    delta = dt2 - dt1
    e1, e2 = 0, 0
    if delta.days < -365.25 * 70:
        e2 = max(int(round((dt1.year - dt2.year) / 100.)) * 100, 0)
    elif delta.days > 365.25 * 70:
        e1 = max(int(round((dt2.year - dt1.year) / 100.)) * 100, 0)
    return e1, e2


def resample_time_series(x, y, period=1):
    """
    Similar to `matplotlib.mlab.griddata(), but in 2D instead of 3D.`
    """
    x = datetime_in_seconds(x)
    x0 = x[0]
    xN = x[-1]
    try:
        period = period.total_seconds()
    except:
        try:
            period = period.days * 3600 * 24 + period.seconds + period.microseconds / 1.e6
        except:
            try:
                period = period.year * 365.25 * 3600 * 24 + period.month * 365.25 / 12. * 3600 * 24 + period.day * 3600 * 24 + period.hour * 3600 + period.minute * 60 + period.second + period.microseconds / 1.e6
            except:
                pass
    N = int((xN - x0) / period)
    #print x0, xN, period, N
    if N > 1000000:
        period *= 84600.
        N = int((xN - x0) / period)
    #print x0, xN, period, N
    if N > 10000:
        period *= 24.
        N = int((xN - x0) / period)
    #print x0, xN, period, N
    k, k1 = 0, 1
    x_new, y_new = [x0 + i * period for i in range(N)], [0.] * N
    for i in range(N):
        #print i
        while x_new[i] > x[k1] and k1 < len(x):
            k1 += 1
            k = k1 - 1
            #print i, k, k1
        dx  = x_new[k1] - x[k]
        slope = float(y[k1] - y[k]) / dx if dx else 0  # TODO: compute slope that, in the next line, will average these two samples that have the same time stamp
        y_new[i] = y[k] + slope * (x_new[i] - x[k])
    return x_new, y_new


def align_time_series(x1, y1, x2, y2, scale_factor=None, x1_epoch=None, x2_epoch=None, x1_monthly=None, x2_monthly=None):
    """
    Creates regularly daily sampled data for two irregularly sampled data_sets, filling the gaps with zeros.

    x1 is considered the 'baseline' sample period. and x2 values not in x1 will have its associated data record ignored

    # TODO: allow x1/x2 to be irregularly sampled too!
    # TODO: allow consolidation into periods other than days (e.g. seconds, minutes, weeks, months, etc)
    """
    if scale_factor is None:
        scale_factor = round_to_sigfigs(best_scale_factor(y1, y2), 0)

    scale_factor = scale_factor or 1
    x1_monthly = x1_monthly or 0
    x2_monthly = x2_monthly or 0
    # For multiple series in a line plot, nvd3 requires us to bin values in a common date (x-axis value)
    if x1_epoch is None or x2_epoch is None:
        try:
            x1_epoch, x2_epoch = guess_epochs(iter(x1).next(), iter(x2).next())
        except StopIteration:
            logger.warn('Unable to align time series if either time series is empty')
            return x1, y1, y2
    N = len(x1)
    z1 = [0] * N
    z2 = [0] * N
    for i, date in enumerate(x1):
        # FIXME: deal with x1 monthly data too!
        day =  date.day * (not x2_monthly) + x2_monthly
        if datetime.date(date.year + x1_epoch - x2_epoch, date.month, day) in x2:
            j = x2.index(datetime.date(date.year + x1_epoch - x2_epoch, date.month, day))
            # FIXME: scale_factor shouldn't be here
            z2[i] = y2[j] * 1.0 / scale_factor
    
    for i, date in enumerate(x1):
        z1[i] = y1[i]


    return x1, z1, z2


def interp_time_series(x1, y1, x2, y2, scale_factor=None, x1_epoch=None, x2_epoch=None, x1_monthly=None, x2_monthly=None):
    """
    Creates regularly daily sampled data for two irregularly sampled data_sets, filling the gaps with interpolated values.

    x1 is considered the 'baseline' sample period. and x2 values not in x1 will have its associated data record ignored

    # TODO: allow x1/x2 to be irregularly sampled too!
    # TODO: allow consolidation into periods other than days (e.g. seconds, minutes, weeks, months, etc)
    """
    scale_factor = scale_factor or 1


    x1_monthly = x1_monthly or 0
    x2_monthly = x2_monthly or 0
    # For multiple series in a line plot, nvd3 requires us to bin values in a common date (x-axis value)
    if x1_epoch is None or x2_epoch is None:
        try:
            x1_epoch, x2_epoch = guess_epochs(iter(x1).next(), iter(x2).next())
        except StopIteration:
            logger.warn('Unable to align time series if either time series is empty')
            return x1, y1, y2
    N = len(x1)
    z1 = [0] * N
    z2 = [0] * N
    for i, date in enumerate(x1):
        # FIXME: deal with x1 monthly data too!
        day =  date.day * (not x2_monthly) + x2_monthly
        if datetime.date(date.year + x1_epoch - x2_epoch, date.month, day) in x2:
            j = x2.index(datetime.date(date.year + x1_epoch - x2_epoch, date.month, day))
            # FIXME: scale_factor shouldn't be here
            z2[i] = y2[j] * 1.0 / scale_factor
    
    for i, date in enumerate(x1):
        z1[i] = y1[i]


    return x1, z1, z2



def passthrough_shaper(x, t=None):
    return x


def windowed_series(series, xmin=None, xmax=None, shaper=None):
    """
    Clip a set of time series (regularly sampled sequences registered to a time value)

    TODO: Incorporate into the nlp.db.Columns class
    
    >>> windowed_series([[-1, 0, 1, 2, 3], [2, 7, 1, 8, 2], [8, 1, 8, 2, 8]], xmin=0, xmax=2)
    [[0, 1, 2], [7, 1, 8], [1, 8, 2]]

    """
    if (xmin, xmax, shaper) is (None, None, None):
        return series

    if xmax is None and xmin is not None:
        xmax = max(series[0])
    elif xmin is None and xmax is not None:
        xmin = min(series[0])
    else:
        ans = series
    
    if None not in (xmin, xmax):
        ans = []
        for i in range(len(series)):
            ans += [[]] 
        if xmin is not None and xmax >= xmin:
            for i, t_i in enumerate(series[0]):
                if xmax >= t_i >= xmin:
                    for j, x in enumerate(series):
                        ans[j] += [x[i]]
    if shaper:
        for i, t_i in enumerate(ans[0]):
            for j, x in enumerate(ans):
                ans[j] += [x[i]]
    return ans




def lagged_gen(seq, lag=1, pad=None, truncate=True):
    """
    Delay a sequence by inserting the specified padding (or deleting samples for a negative lag).

    if pad = None then wrap (mod) the sequence to maintain the same length

    TODO: Add ability to handle fractional sample lags using interpolation
    TODO: Incorporate as a method in the nlp.db.Columns class
    TODO: Avoid conversion to a list before iterating through (just iterate through twice and yield)
    
    >>> list(lagged_gen([2, 7, 1, 8, 2, 8, 1, 8, 2, 8]))
    [8, 2, 7, 1, 8, 2, 8, 1, 8, 2]
    >>> list(lagged_gen([2, 7, 1, 8, 2, 8, 1, 8, 2, 8], lag=-2, pad=0))
    [1, 8, 2, 8, 1, 8, 2, 8, 0, 0]
    """
    lag = int(lag or 0)
    # defeats the purpose of a generator, but...
    lst = list(seq)
    N = len(lst)
    if pad is None:
        lag = N - lag
        for i in range(N):
            yield lst[(i + lag) % N]
    else:
        pad_element = [pad]
        lst = int(lag > 0) * (pad_element * lag) + lst + int(lag < 0) * (pad_element * abs(lag))
        if truncate:
            if lag > 0:
                lst = lst[:-lag]
            elif lag < 0:
                lst = lst[-lag:]
        for i, value in enumerate(lst):
            yield value


def lagged_seq(seq, lag=1, pad=None, truncate=True):
    return list(lagged_gen(seq, lag, pad, truncate))


def lagged_series(series, lags=1, pads=None):
    """
    Delay each time series in a set of time series by the lags (number of samples) indicated.

    Pad any gaps in the resulting series with the value of pads or clip, if None.


    TODO: Allow fractional sample lags (interpolation)
    TODO: Allow time value lags instead of sample counts
    TODO: Incorporate into the nlp.db.Columns class
    
    >>> lagged_series([[-1, 0, 1, 2, 3], [2, 7, 1, 8, 2], [8, 1, 8, 2, 8]], lags=3)
    [[-1, 0, 1, 2, 3], [1, 8, 2, 2, 7], [8, 2, 8, 8, 1]]
    >>> lagged_series([[-1, 0, 1, 2, 3], [2, 7, 1, 8, 2], [8, 1, 8, 2, 8]], lags=[2, 1], pads=0)
    [[-1, 0, 1, 2, 3], [0, 0, 2, 7, 1], [0, 8, 1, 8, 2]]
    >>> lagged_series([[-1, 0, 1, 2, 3], [2, 7, 1, 8, 2], [8, 1, 8, 2, 8]], lags=[-1, 3], pads=[-9, -5])
    [[-1, 0, 1, 2, 3], [7, 1, 8, 2, -9], [-5, -5, -5, 8, 1]]
    """
    N = len(series) - 1
    pads = [None] * N if pads is None else util.listify(pads, N)
    pads = [None] + pads
    lags = [None] * N if lags is None else util.listify(lags, N)
    lags = [None] + lags

    ans = [series[0]]

    for i in range(1, min(len(lags) + 1, len(pads) + 1, N + 1)):
        #print pads[i]
        ans += [lagged_seq(series[i], lags[i], pads[i])]

    return ans


def replace_nonascii(s, filler='', one_for_one=False):
    '''Remove nonASCII characters from provided string

    Based on: http://stackoverflow.com/a/2743163/623735 
              by [Khelben](http://stackoverflow.com/users/205083/khelben)
          and
              http://stackoverflow.com/a/20078869/623735
              by [Martin Pieters](http://stackoverflow.com/users/100297/martijn-pieters)

    >>> replace_nonascii(u'éáé123456tgreáé@€')
    u'123456tgre@'
    >>> replace_nonascii('\xFE\xFF\xEF\xBB\xBF\xFF\xFE\x00\x00\x81\x9F':)
    ''
    '''
    if one_for_one:
        return regex_patterns.nonascii.sub(filler, s)
    return regex_patterns.nonascii_sequence.sub(filler, s)


def strip_nonascii(s):
    return replace_nonascii(s, filler='')


def clean_utf8(byte_seq, carefully=False, encodings_to_try=('CP-1252', 'shift-jis', 'ISO-8859-2', 'utf8', 'shift-jis-2004', 'iso-8859-1', 'utf16'), verbosity=0):
    r"""Delete any invalid symbols in a UTF-8 encoded string

    Returns:
      str: `byte_seq` encoded in UTF-8, e.g. `unicode(byte_seq).encode('utf-8')`

    Arguments:
      encodings_to_try (list of str): List of encodings to use to attempt to decode the byte sequence, listed in priority order.
        default: = ['shift-jis', 'ISO-8859-2', 'utf8', 'shift-jis-2004', 'CP-1252', 'iso-8859-1', 'utf16']
          'shift-jis': Japanese corporate data in MS SQL databases is often encoded in Shift JIS
          'CP1252' : Legacy microsoft windows SQLServer that seems to work for u'\xff\xfe' line terminations
          'SQL_Latin1_General_CP1_CI_AS': A case-insensitive mix of CP-1252 and UTF-8 common among Japanese corporations
          'iso-8859-1' : MS SQL Server default encoding (before 2008)
          'iso-8859-2' : MS SQL Server default encoding (before 2012)

    Examples:
      >>> clean_utf8('`A\xff\xffBC\x7fD\tE\r\nF~G`')
      '`A\xc3\xbf\xc3\xbfBC\x7fD\tE\r\nF~G`'
      >>> clean_utf8('`A\xff\xffBC\x7fD\tE\r\nF~G`').decode('UTF8')
      u'`A\xff\xffBC\x7fD\tE\r\nF~G`'
      >>> clean_utf8('`A\xff\xffBC\x7fD\tE\r\nF~G`', carefully=True)
      '`ABC\x7fD\tE\r\nF~G`'
      >>> clean_utf8('U\xc2\xa0\xc2\xa0\xc2\xa0\xc2\xa0\xc2').decode('UTF8')
    """
    #print 'cleaning: ' + repr(byte_seq)
    if not isinstance(byte_seq, basestring):
        return byte_seq
    for enc in encodings_to_try:
        try:
            return unicode(byte_seq.decode(enc)).encode('utf8')
        except UnicodeDecodeError:
            if verbosity > 1:
                print("Unable to short-circuit clean_utf8 function with try {0}.decode({1})".format(byte_seq, enc))
    if carefully:
        while True:
            try:
                byte_seq.decode('utf8')
                # json.dumps(byte_seq)
                break
            except UnicodeDecodeError as e:
                    if verbosity:
                        print 'UnicodeDecodeError: %s' % str(e)
                    m = re.match(r".*can't[ ]decode[ ]byte[ ]0x[0-9a-fA-F]{2}[ ]in[ ]position[ ](\d+)[ :.].*", str(e))
                    if m and m.group(1):
                        i = int(m.group(1))
                        byte_seq = byte_seq[:i] + byte_seq[i+1:]
                    else:
                        raise e
            except UnicodeEncodeError:
                if verbosity:
                    'cleaned carefully and got UnicodeEncodeError, left with: %r' % unicode(byte_seq)
                return unicode(byte_seq)
        if verbosity:
            'cleaned carefully and came up with: %r' % unicode(byte_seq)
        return byte_seq
    else:
        diagnosis = {'encoding': None, 'confidence': -1}
        try:
            diagnosis = chardet.detect(byte_seq)
        except:
            if verbosity:
                from traceback import print_exc
                print_exc()
        if verbosity:
            print diagnosis
        if diagnosis['confidence'] > 0.25:
            try:
                # FIXME: should this be unicode instead of str?
                return unicode(byte_seq.decode(diagnosis['encoding']).encode('utf8'))
            except:
                pass
        for encoding in encodings_to_try[1:]:
            try:
                return unicode(byte_seq.decode(encoding).encode('utf8'))
            except:
                pass
        return clean_utf8(byte_seq, carefully=True)


