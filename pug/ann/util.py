"""Utilities for maniuplating, analyzing and plotting `pybrain` `Network` and `DataSet` objects

TODO:
    Incorporate into pybrain fork so pug doesn't have to depend on pybrain

"""
import os

import pandas as pd
from matplotlib import pyplot as plt

from pybrain.supervised import trainers


def plot_trainer(trainer, ds=None, mean=0, std=1, name='', show=True, save=True):
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
    plt.title(name)

    if show:
        plt.show(block=False)
    if save:
        filename = 'ann_performance_for_{0}.png'.format(name).replace(' ', '_')
        if isinstance(save, basestring) and os.path.isdir(save):
            filename = os.path.join(save, filename) 
        plt.savefig(filename)
    if not show:
        plt.clf()

    return trainer, mean, std

