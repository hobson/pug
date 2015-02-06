"""Utilities for maniuplating, analyzing and plotting `pybrain` `Network` and `DataSet` objects

TODO:
    Incorporate into pybrain fork so pug doesn't have to depend on pybrain

"""
import os

import pandas as pd
from matplotlib import pyplot as plt


def plot_network_results(network, ds=None, mean=0, std=1, title='', show=True, save=True):
    """Identical to plot_trainer except `network` and `ds` must be provided separately"""
    df = sim_network(network=network, ds=ds, mean=mean, std=std)
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

    return network, mean, std


def trainer_results(trainer, mean=0, std=1, title='', show=True, save=True):
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
    return plot_network_results(network=trainer.module, ds=trainer.ds, mean=mean, std=std, title=title, show=show, save=save)




def sim_trainer(trainer, mean=0, std=1):
    """Simulate a trainer by activating its DataSet and returning DataFrame(columns=['Output','Target'])
    """
    return sim_network(network=trainer.module, ds=trainer.ds, mean=mean, std=std)


def sim_network(network, ds=None, index=None, mean=0, std=1):
    """Simulate/activate a Network on a SupervisedDataSet and return DataFrame(columns=['Output','Target'])

    The DataSet's target and output values are denormalized before populating the dataframe columns:

        denormalized_output = normalized_output * std + mean

    Which inverses the normalization that produced the normalized output in the first place: 

        normalized_output = (denormalzied_output - mean) / std

    Args:
        network (Network): a pybrain Network instance to activate with the provided DataSet, `ds`
        ds (DataSet): a pybrain DataSet to activate the Network on to produce an output sequence
        mean (float): mean of the denormalized dataset (default: 0)
          Output is scaled
        std (float): std (standard deviation) of the denormalized dataset (default: 1)
        title (str): title to display on the plot.

    Returns:
        DataFrame: DataFrame with columns "Output" and "Target" suitable for df.plot-ting
    """
    # just in case network is a trainer or has a Module-derived instance as one of it's attributes
    if hasattr(network, 'module') and hasattr(network.module, 'activate'):  # isinstance(network.module, (networks.Network, modules.Module))
        network = network.module
    ds = ds or network.ds
    if not ds:
        raise RuntimeError("Unable to find a `pybrain.DataSet` instance to activate the Network with in order to plot the outputs. A dataset can be provided as part of a network instance or as a separate kwarg if `network` is used to provide the `pybrain.Network` instance directly.")
    results_generator = ((network.activate(ds['input'][i])[0] * std + mean, ds['target'][i][0] * std + mean) for i in xrange(len(ds['input'])))
    
    return pd.DataFrame(results_generator, columns=['Output', 'Target'], index=index or range(len(ds['input'])))
