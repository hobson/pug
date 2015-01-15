import numpy as np
import pandas as pd

from nlp.util import listify

from matplotlib import pyplot as plt
from matplotlib import animation

def period_boxplot(df, period='year', column='Adj Close'):
    # df['period'] = df.groupby(lambda t: getattr(t, period)).aggregate(np.mean)
    df['period'] = getattr(df.index, period)
    perioddata = df.pivot(columns='period', values=column)
    perioddata.boxplot()
    plt.show()


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