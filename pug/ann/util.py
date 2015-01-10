"""Utilities for maniuplating, analyzing and plotting `pybrain` `Network` and `DataSet` objects

TODO:
    Incorporate into pybrain fork so pug doesn't have to depend on pybrain

"""
import os

import pandas as pd
from matplotlib import pyplot as plt

from pybrain.supervised import trainers


def plot_trainer(trainer, ds=None, mean=0, std=1, title='', show=True, save=True):
    """Plot the performance of the Network and SupervisedDataSet in a pybrain Trainer

    DataSet target and output values are denormalized before plotting with:

        output * std + mean

    Which inverses the normalization 

        (output - mean) / std

    Args:
        trainer (Trainer): a pybrain Trainer instance containing a valid Network and DataSet
        ds (DataSet): a pybrain DataSet to override the one contained in `trainer`. 
          Required if trainer is a Network instance rather than a Trainer instance.
        mean (float): mean of the denormalized dataset (default: 0)
          Only affects the scale of the plot
        std (float): std (standard deviation) of the denormalized dataset (default: 1)
        title (str): title to display on the plot.

    Returns:
        3-tuple: (trainer, mean, std), A trainer/dataset along with denormalization info
    """
    if isinstance(trainer, trainers.Trainer):
        ann = trainer.module
        ds = ds or trainer.ds
    elif not ds:
        raise RuntimeError("Unable to find a `pybrain.DataSet` instance to run the ANN on for plotting the results. A dataset can be provided as part of a trainer instance or as a separate kwarg if `trainer` is used to provide the `pybrain.Network` instance directly.")
    results = [(ann.activate(ds['input'][i])[0] * std + mean, ds['target'][i][0] * std + mean) for i in range(len(ds['input']))]
    df = pd.DataFrame(results, columns=['Predicted', 'Optimal'])
    df.plot()  
    plt.xlabel('Date')
    plt.ylabel('Threshold (kW)')
    plt.title(title)

    if show:
        plt.show(block=False)
    if save:
        filename = 'ann_performance_for_{0}.png'.format(title).replace(' ', '_')
        if isinstance(save, basestring) and os.path.isdir(save):
            filename = os.path.join(save, filename) 
        plt.savefig(filename)
    if not show:
        plt.clf()

    return trainer, mean, std

def plot_network(network, ds, mean=0, std=1, title='', show=True, save=True):
    """Identical to plot_trainer except `network` and `ds` must be provided separately"""
    return plot_trainer(trainer=network, ds=ds, mean=mean, std=std, title=title, show=show, save=save)