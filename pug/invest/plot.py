from __future__ import print_function, division
import six

import datetime
import os
from collections import Counter, OrderedDict
from traceback import print_exc

import numpy as np
import pandas as pd

from pug.nlp.util import listify, make_datetime, ordinal_float, quantize_datetime

from matplotlib import pyplot as plt
from matplotlib import animation


def period_boxplot(df, period='year', column='Adj Close'):
    # df['period'] = df.groupby(lambda t: getattr(t, period)).aggregate(np.mean)
    df['period'] = getattr(df.index, period)
    perioddata = df.pivot(columns='period', values=column)
    perioddata.boxplot()
    plt.show()


def animate_panel(panel, keys=None, columns=None, interval=1000, blit=False, titles='', path='animate_panel', xlabel='Time', ylabel='Value', ext='gif', 
                  replot=False, linewidth=3, close=False, fontsize=24, background_color='white', alpha=1, figsize=(12,8), xlabel_rotation=-25, plot_kwargs=(('rotation', 30),), **video_kwargs):
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
    >>> ani = animate_panel(panel, interval=200, path='animate_panel_test')  # doctest: +ELLIPSIS
    <matplotlib.animation.FuncAnimation at ...>
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
        print('init')
        df = panel[0]
        x = df.index.values
        y = df[columns].values.T
        for i in range(len(lines)):
            # FIXME: why are x-values used to set the y-data coordinates of the mask?
            lines[i].set_xdata(np.ma.array(x, mask=True))
            lines[i].set_ydata(np.ma.array(y[i], mask=True))
        return lines

    print('Drawing frames for a ".{0}" animation{1}...'.format(ext, ' with blitting' if blit else ''))
    animate(keys[0])
    ani = animation.FuncAnimation(fig, animate, keys, interval=interval, blit=blit) #, init_func=mask_lines, blit=True)

    kwargs = dict(default_kwargs)
    for k, v in six.iteritems(default_kwargs):
        kwargs[k] = video_kwargs.get(k, v)
    # if 'bitrate' in kwargs:
    #     kwargs['bitrate'] = min(kwargs['bitrate'], int(8e5 / interval))  # low information rate (long interval) might make it impossible to achieve a higher bitrate ight not
    if path and isinstance(path, basestring):
        path += '.{0}'.format(ext)
        print('Saving video to {0}...'.format(path))
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




def plot_histogram(df, column=0, width=0.9, resolution=2, str_timetags=True, 
                   xlabel=None, date_sep='-', bins=None, 
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

    FIXME:
      - fail for `label_len=7`
    """
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
    if isinstance(df, basestring) and os.path.isfile(df):
        df = pd.DataFrame.from_csv(df)
    if isinstance(column, int):
        column = df.columns[column]
    xlabel = xlabel or column or ''
    his0, his1 = [], []
    if str_timetags and any(isinstance(val, basestring) for val in df[column].values):
        timetag = [datetime.datetime.strptime(val, '%m/%d/%Y') if isinstance(val, basestring) else make_datetime(val) for val in df[column]]
        # r['Returned Ordinal'] = [datetime.datetime.strptime(s, '%m/%d/%Y').date().toordinal() for s in r['Returned']]
        quantized_date = [quantize_datetime(dt, resolution) for dt in timetag]
        quantized_ordinal = ordinal_float(quantized_date)
        if not bins:
            his0, his1 = zip(*sorted(Counter(quantized_ordinal).items()))
            bins = his0
        else:
            his1, his0 = pd.np.histogram(ordinal_float(df[column].dropna()), bins=bins)
        resolution = int(resolution or 7)
        labels = [date_sep.join(str(val) for val in datetime.datetime.fromordinal(ordinal).timetuple()[:resolution]) for ordinal in his0]
    bins = bins or resolution * 10
    try:
        if len(bins) == 2:
            bins = list(bins)
            values = df[column].dropna()

            binwidth = ((bins[1]-bins[0]) or 1)
            if not bins[0] and (values.max() - values.min()) > 10 * binwidth:
                bins[0] = values.min()
            xscale = (values.max() - bins[0])
            numbins = int(xscale / float(binwidth)) + 2
            bins = list(pd.np.arange(numbins) * binwidth + bins[0])
    except:
        print_exc()
    if isinstance(df[column].values[0], (float, int)):
        his1, his0 = pd.np.histogram(df[column].dropna(), bins=bins)
        labels = ['{:.3g}'.format(val) for val in his0[:-1]]
        # labels = ['{:.3g}-{.3g}'.format(left, right) for left, right in zip(his[0][:-1], his[0][1:])]
        width = max(width, 0.95)
        padding = 0
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

    xwidth = (width or 0.9) * pd.np.diff(his0).min()

    if not isinstance(ylabel, basestring):
        ylabel = 'Count (Number of Occurrences)'
    ax.bar(his0, his1, width=xwidth, color=color, alpha=alpha)

    plt.xticks([dy + padding*xwidth for dy in his0], labels, rotation=rotation, ha=ha)
    plt.xlabel(column)
    plt.ylabel(ylabel)
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
    his0 = pd.np.array(his0)
    return (his0, his1), labels