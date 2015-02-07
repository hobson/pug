from __future__ import print_function, division
import six

import datetime
import os
from collections import Counter, OrderedDict
from traceback import print_exc
import warnings

import numpy as np
import pandas as pd

from pug.nlp.util import listify, make_datetime, ordinal_float, quantize_datetime, datetime_from_ordinal_float, is_valid_american_date_string

from matplotlib import pyplot as plt
from matplotlib import animation


def period_boxplot(df, period='year', column='Adj Close'):
    # df['period'] = df.groupby(lambda t: getattr(t, period)).aggregate(np.mean)
    df['period'] = getattr(df.index, period)
    perioddata = df.pivot(columns='period', values=column)
    perioddata.boxplot()
    plt.show()


def animate_panel(panel, keys=None, columns=None, interval=1000, blit=False, titles='', path='animate_panel', xlabel='Time', ylabel='Value', ext='gif', 
                  replot=False, linewidth=3, close=False, fontsize=24, background_color='white', alpha=1, figsize=(12,8), xlabel_rotation=-25, plot_kwargs=(('rotation', 30),), 
                  verbosity=1, **video_kwargs):
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

    TODO: 
      - Work with other 3-D data formats:
          - dict (sorted by key) or OrderedDict
          - list of 2-D arrays/lists
          - 3-D arrays/lists
          - generators of 2-D arrays/lists
          - generators of generators of lists/arrays?
      - Write json and html5 files for d3 SVG line plots with transitions!

    >>> x = np.arange(0, 2*np.pi, 0.05)
    >>> panel = pd.Panel(dict((i, pd.DataFrame({
    ...        'T=10': np.sin(x + i/10.),
    ...        'T=7': np.sin(x + i/7.),
    ...        'beat': np.sin(x + i/10.) + np.sin(x + i/7.),
    ...        }, index=x)
    ...    ) for i in range(50)))
    >>> animate_panel(panel, interval=200, path='animate_panel_test')  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    Drawing frames for a ".gif" animation...
    Saving video to animate_panel_test.gif...
              T=10       T=7      beat
    0.00  0.000000  0.000000  0.000000
    0.05  0.049979  0.049979  0.099958
    ...

    [126 rows x 3 columns]
    """
    plot_kwargs = plot_kwargs or {}
    plot_kwargs = dict(plot_kwargs)
    ext_kwargs = {
        'mp4': {'writer': 'ffmpeg', 'codec': 'mpeg4', 'dpi': 100, 'bitrate': 2000},
        'gif': {'writer': 'imagemagick', 'dpi': 100, 'bitrate': 2000},
        'imagemagic.gif': {'writer': 'imagemagick_gif', 'dpi': 100, 'bitrate': 2000},
        }
    ext = str(ext).lower().strip() or 'gif'
    default_kwargs = ext_kwargs.get(ext, {})

    keys = keys or list(panel.keys())
    if titles:
        titles = listify(titles)
        if len(titles) == 1:
            titles *= len(keys)
    else:
        titles = keys
    titles = dict((k, title) for k, title in zip(keys, titles))
    columns = columns or list(panel[keys[0]].columns)
    
    fig, ax = plt.subplots(figsize=figsize)

    fig.patch.set_facecolor(background_color)
    fig.patch.set_alpha(alpha)


    i = 0
    df = panel[keys[i]]
    x = df.index.values
    y = df[columns].values
    lines = ax.plot(x, y)
    ax.grid('on')
    ax.patch.set_facecolor(background_color)
    ax.patch.set_alpha(alpha)
    ax.title.set_text(titles[keys[0]])
    ax.title.set_fontsize(fontsize)
    ax.title.set_fontweight('bold')
    ax.xaxis.label.set_text(xlabel)
    plt.setp(ax.get_xticklabels(), rotation=xlabel_rotation)
    ax.yaxis.label.set_text(ylabel)
    ax.legend(columns)


    def animate(k):
        df = panel[k]
        x = df.index.values
        y = df[columns].values.T
        if replot:
            # plt.cla()
            # fig, ax = plt.subplots(figsize=figsize)
            fig = ax.figure
            fig.patch.set_facecolor(background_color)
            fig.patch.set_alpha(alpha)
            lines = ax.plot(x, y.T, linewidth=linewidth)
            ax.grid('on')
            ax.patch.set_facecolor(background_color)
            ax.patch.set_alpha(alpha)
            ax.title.set_text(titles[k])
            ax.title.set_fontsize(fontsize)
            ax.title.set_fontweight('bold')
            ax.xaxis.label.set_text(xlabel)
            plt.setp(ax.get_xticklabels(), rotation=xlabel_rotation)
            ax.yaxis.label.set_text(ylabel)
            ax.legend(columns)
        else:
            lines = ax.lines
            fig = ax.figure

            for i in range(len(lines)):
                lines[i].set_xdata(x)  # all lines have to share the same x-data
                lines[i].set_ydata(y[i])  # update the data, don't replot a new line
                lines[i].set_linewidth(linewidth)
                lines[i].figure.set_facecolor(background_color)
                lines[i].figure.set_alpha(alpha)
                lines[i].axes.patch.set_facecolor(background_color)
                lines[i].axes.patch.set_alpha(alpha)
            ax.patch.set_facecolor(background_color)
            ax.figure.patch.set_alpha(alpha)
            ax.title.set_text(titles[k])
            ax.title.set_fontsize(fontsize)
            ax.title.set_fontweight('bold')
        if blit:
            return lines

    # FIXME: doesn't work with ext=mp4
    # init_func to mask out pixels to be redrawn/cleared which speeds redrawing of plot
    def mask_lines():
        if verbosity:
            print('Initialing mask_lines. . .')
        df = panel[0]
        x = df.index.values
        y = df[columns].values.T
        for i in range(len(lines)):
            # FIXME: why are x-values used to set the y-data coordinates of the mask?
            lines[i].set_xdata(np.ma.array(x, mask=True))
            lines[i].set_ydata(np.ma.array(y[i], mask=True))
        return lines

    if verbosity:
        print('Drawing frames for a ".{0}" animation{1}. . .'.format(ext, ' with blitting' if blit else ''))
    animate(keys[0])
    ani = animation.FuncAnimation(fig, animate, keys, interval=interval, blit=blit) #, init_func=mask_lines, blit=True)

    kwargs = dict(default_kwargs)
    for k, v in six.iteritems(default_kwargs):
        kwargs[k] = video_kwargs.get(k, v)
    # if 'bitrate' in kwargs:
    #     kwargs['bitrate'] = min(kwargs['bitrate'], int(8e5 / interval))  # low information rate (long interval) might make it impossible to achieve a higher bitrate ight not
    if path and isinstance(path, basestring):
        path += '.{0}'.format(ext)
        if verbosity:
            print('Saving video to {0}. . .'.format(path))
        ani.save(path, **kwargs)

    if close:
        plt.close(fig)
    return df


def percent_formatter(y_value, y_position):
    s = ('{0:.' + str(int(percent_formatter.precision)) + 'g}').format(percent_formatter.scale_factor * y_value)
    # escape the percent symbol if TeX string preprocessing is being used
    s += r'$\%$' if plt.rcParams.get('text.usetex', False) == True else '%'
    return s
percent_formatter.scale_factor = 100
percent_formatter.precision = 0


DATETIME_KWARGS = OrderedDict([('year', 1970), ('month', 1), ('day', 1), ('hour', 0), ('minute', 0), ('second', 0), ('microsecond', 0)])


def generate_bins(bins, values=None):
    """Compute bin edges for numpy.histogram based on values and a requested bin parameters

    Unlike `range`, the largest value is included within the range of the last, largest value,
    so generate_bins(N) with produce a sequence with length N+1

    Arguments:
        bins (int or 2-tuple of floats or sequence of floats) s or the first pair of bin edges

    >>> generate_bins(0, [])
    [0]
    >>> generate_bins(3, [])
    [0, 1, 2, 3]
    >>> generate_bins(0)
    [0]
    >>> generate_bins(10)
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    >>> generate_bins(10, range(21))
    [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0]
    >>> generate_bins((0, 3), range(21))
    [0, 3, 6, 9, 12, 15, 18, 21]
    """
    if isinstance(bins, int):
        bins = (bins,)
    if isinstance(bins, float):
        bins = (0, bins)

    if not len(bins) in (1, 2):
        return bins

    if values in (None, [], ()) or not hasattr(values, '__iter__') or not any(values):
        values = [0]
    value_min, value_max = pd.np.min(values), pd.np.max(values)
    value_range = value_max - value_min

    if len(bins) == 1:
        if not value_range:
            return range(int(bins[0]) + 1)
        bins = (0, value_range / float(bins[0]))
    if len(bins) == 2:
        if not value_range:
            return bins
        binwidth = ((bins[1] - bins[0]) or 1)
        bin0 = bins[0] or pd.np.min(values)
        if (bin0 / value_range) <= .3:
            bin0 = 0
        numbins = int(value_range / float(binwidth))
        bins = list(pd.np.arange(numbins + 1) * binwidth + bin0)
    else:
        binwidth = pd.np.min(pd.np.diff(bins)) or pd.np.mean(pd.np.diff(bins)) or 1.
    bins = list(bins)
    while bins[-1] < value_max:
        bins.append(bins[-1] + binwidth)
    return bins


def thin_string_list(list_of_strings, max_nonempty_strings=50, blank=''):
    """Designed for composing lists of strings suitable for pyplot axis labels

    Often the xtick spacing doesn't allow room for 100's of text labels, so this
    eliminates every other one, then every other one of those, until they fit.

    >>> thin_string_list(['x']*20, 5)  # doctring: +NORMALIZE_WHITESPACE
    ['x', '', '', '', 'x', '', '', '', 'x', '', '', '', 'x', '', '', '', 'x', '', '', '']
    """
        # blank some labels to make sure they don't overlap
    list_of_strings = list(list_of_strings)
    istep = 2
    while sum(bool(s) for s in list_of_strings) > max_nonempty_strings:
        list_of_strings = [blank if i % istep else s for i, s in enumerate(list_of_strings)]
        istep += 2
    return list_of_strings


def plot_histogram(hist, width=0.9,
                   title='', xlabel=None, date_sep='-',
                   labels=None, color=None, alpha=None, normalize=True, percent=False, padding=0.03,
                   formatter=None, ylabel_precision=2, resolution=3,
                   figsize=None, line_color='#C0C0C0', bg_color='white', bg_alpha=1, tight_layout=True,
                   ylabel=None, grid='on', rotation=-60, ha='left',
                   save_path='plot_histogram', dpi=200):
    """Plot a bar chart from np.histogram data

    >>> plot_histogram(np.histogram([1]*5+[3]*2+list(range(20))+[19.1]), alpha=1)  # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
    ((array([7, 4, 2, 2, 2, 2, 2, 2, 2, 3]),
    array([  0.  ,   1.91,   3.82,   5.73,   7.64,   9.55,  11.46,  13.37,
        15.28,  17.19,  19.1 ])),
    <matplotlib.figure.Figure at ...)
    """
    his0, his1 = hist[0], hist[1]
    if len(his1) == len(his0) + 1:
        his0, his1 = his1[:-1], his0
    elif len(his0) == len(his1) + 1:
        his0 = his0[:-1]

    resolution = resolution or 3
    if labels in (None, 0, 'date', 'datetime'):
        try:
            labels = [date_sep.join(str(val) for val in datetime_from_ordinal_float(val).timetuple()[:resolution]) for val in his0]
        except:
            labels = [('{0:.' + str(resolution) + 'g}').format(val) for val in his0]
    elif labels == False:
        labels = [''] * len(his0)
    if len(labels) != len(his0) or not all(isinstance(val, basestring) for val in labels):
        labels = list(str(s) for s in labels)
        labels += [''] * (len(his0) - len(labels))
    
    labels = thin_string_list(labels, 50)

    fig = plt.gcf()
    if figsize and len(figsize)==2:
        fig.set_size_inches(figsize[0], figsize[1], forward=True)
    if bg_color or bg_alpha:
        fig.set_facecolor(bg_color)
        fig.set_alpha(bg_alpha)
    if not fig.axes:
        ax = fig.add_subplot(111)
    else:
        ax = fig.gca()

    color = color or 'b'
    alpha = alpha or .8
    xlabel = xlabel or ''

    xwidth = (width or 0.9) * pd.np.min(pd.np.diff(his0))

    if not isinstance(ylabel, basestring):
        ylabel = 'Count (Number of Occurrences)'


    xwidth = (width or 0.9) * pd.np.min(pd.np.diff(his0))

    ax.bar(his0, his1, width=xwidth, color=color, alpha=alpha)

    print(his0)
    plt.xticks([dy + padding*xwidth for dy in his0], labels, rotation=rotation, ha=ha)
    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)
    if title:
        plt.title(title)
    if formatter and callable(formatter):
        ax.yaxis.set_major_formatter(plt.matplotlib.ticker.FuncFormatter(formatter))
    ax.grid(grid, color=(line_color or 'gray'))

    # set all the colors and transparency values 
    fig.patch.set_facecolor(bg_color)
    fig.patch.set_alpha(bg_alpha)
    ax.patch.set_alpha(bg_alpha)
    ax.patch.set_facecolor(bg_color)

    if line_color:
        for spine in ax.spines.values():
            spine.set_color(line_color)
        ax.tick_params(axis='x', colors=line_color)
        ax.tick_params(axis='y', colors=line_color)
        ax.xaxis.label.set_color(line_color)
        ax.yaxis.label.set_color(line_color)
        ax.title.set_color(line_color)

    if tight_layout:
        plt.tight_layout()

    try:
        plt.show(block=False)
    except:
        print_exc()

    if save_path:
        if os.path.isfile(save_path + '.png'):
            i = 2
            save_path2 = save_path + '--{0}'.format(i)
            while os.path.isfile(save_path2 + '.png'):
                i += 1
                save_path2 = save_path + '--{0}'.format(i)
            save_path = save_path2
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=dpi)

    # return in standard numpy histogram format, values before bins, and bins include all fenceposts (edges)
    his0, his1 = pd.np.array(his0), pd.np.array(his1)
    his0 = np.append(his0, 2 * his0[-1] - his0[-2])
    return (his1, his0), fig


def histogram_and_plot(df, column=0, width=0.9, resolution=2, str_timetags=True, counted=False,
                   title='', xlabel=None, date_sep='-', bins=None, 
                   labels=None, color=None, alpha=None, normalize=True, percent=False, padding=0.03,
                   formatter=None, ylabel_precision=2,
                   figsize=None, line_color='#C0C0C0', bg_color='white', bg_alpha=1, tight_layout=True,
                   ylabel=None, grid='on', rotation=-60, ha='left',
                   save_path='plot_histogram', dpi=200):
    """Bin a DataFrame of floats or datetime strings and plot the histogram

    Arguments:
      df (DataFrame of str or float): table of data containing data to be counted and binned
      column (str): label of the DataFrame column containing data to be counted and binned
      width (float): 0 < width <= 1, the graphical width of the bars as a fraction of the bin width
      resolution (int): 0 < resolution < 7, 
        for a number of timetuple fields to truncate to for binning 
    TODO:
      - allow more than one column/field/series
      - add of cumulative histogram line overlay
      - separate out plotting from counting and datetime conversion

    FIXME:
      - fail for `label_len=7`
    """

    try:
        assert(len(bins) == len(counted) + 1)
        his0, his1 = bins, counted
    except:
        his0, his1 = [], []

        if isinstance(df, basestring) and os.path.isfile(df):
            df = pd.DataFrame.from_csv(df)
        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)
        if isinstance(column, int):
            column = df.columns[column]
        if not column in df.columns:
            if not column == 'index':
                warnings.warn('Unable to find a column named {0}, so using the index named "{1}" instead. The available columns are:\n{2}'.format(
                    column, df.index.name, df.columns))
            column = df.index.name
        if column == df.index.name:
            df[column] = df.index.values

    if not len(his0) and not len(his1) and not isinstance(df[column].dropna().values[0], (float, int)):
        if all(isinstance(val, (datetime.datetime, datetime.date, datetime.time, pd.Timestamp, pd.np.datetime64)) for val in df[column].dropna().values):
            timetag = df[column].values
        elif str_timetags and all(is_valid_american_date_string(val) for val in df[column].dropna().values):
            timetag = [datetime.datetime.strptime(val, '%m/%d/%Y') if isinstance(val, basestring) else make_datetime(val) for val in df[column]]
        else:
            timetag = [make_datetime(val) for val in df[column].values]

        # r['Returned Ordinal'] = [datetime.datetime.strptime(s, '%m/%d/%Y').date().toordinal() for s in r['Returned']]
        if resolution and bins in (None, 0):
            quantized_date = [quantize_datetime(dt, resolution) for dt in timetag]
            quantized_ordinal = ordinal_float(quantized_date)
            his0, his1 = zip(*sorted(Counter(quantized_ordinal).items()))
            bins = his0
        else:
            days = ordinal_float(df[column].dropna())
            bins = generate_bins(bins, days)
            his1, his0 = pd.np.histogram(days, bins=bins)
            
        resolution = int(resolution or 7)

    if counted in (None, 0, False, []):
        if any(his0) and any(his1):
            labels = [date_sep.join(str(val) for val in datetime_from_ordinal_float(ordinal).timetuple()[:resolution]) for ordinal in his0]
        elif isinstance(df[column].values[0], (float, int)):
            if not any(bins):
                bins = resolution * 10
            bins = generate_bins(bins, df[column].dropna())
            his1, his0 = pd.np.histogram(df[column].dropna(), bins=bins)
            labels = ['{:.3g}'.format(val) for val in his0[:-1]]
            # labels = ['{:.3g}-{.3g}'.format(left, right) for left, right in zip(his[0][:-1], his[0][1:])]
            width = max(width, 0.95)
            padding = 0

    if len(his0) > len(his1):
        his0 = his0[:-1]
    his0 = pd.np.array(his0)
    his1 = pd.np.array(his1)
    if normalize:
        normalize = float(normalize)
        total = float(pd.np.sum(his1))
        his1 = normalize * his1 * 1.0 / total
        if not isinstance(ylabel, basestring):
            if normalize in (1., 100.):
                ylabel = 'Frequency (Probability or Count/Total)'
                if not (formatter and callable(formatter)):
                    formatter = percent_formatter
                    if normalize != 1.:
                        percent_formatter.scale_factor = 1.
                        percent_formatter.precision = ylabel_precision
                        normalize = 1.
            else:
                ylabel = 'Scaled Frequency ({0:.6g}*Count/Total)'.format(normalize)

    return plot_histogram( hist=(his0, his1), width=width,
                           title=title, xlabel=xlabel, date_sep=date_sep, 
                           labels=labels, color=color, alpha=alpha, normalize=normalize, percent=percent, padding=padding,
                           formatter=formatter, ylabel_precision=ylabel_precision,
                           figsize=figsize, line_color=line_color, bg_color=bg_color, bg_alpha=bg_alpha, tight_layout=tight_layout,
                           ylabel=ylabel, grid=grid, rotation=rotation, ha=ha,
                           save_path=save_path, dpi=dpi)