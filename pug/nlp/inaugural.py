# -*- coding: utf-8 -*-
from __future__ import division

import os
from math import log, e
from collections import Mapping
import json

import nltk
import numpy as np

import character_subset as ascii

DEFAULT_FILE_LIST = os.listdir('inaugural')


def score_words_in_files(filenames=DEFAULT_FILE_LIST[:14], entropy_threshold=0.99):
    """Calculate relevance score for words in a set of files

    score_words_in_files(filenames=DEFAULT_FILE_LIST, entropy_threshold=0.9):
        return scores, occurrence_matrix, filenames, most_relevant_words
    """

    filtered_filenames = []

    Text = []     # list of tokened texts
    Total = []    # all texts put together 
    Speech_Length = []
    
    print 'Reading %s files' % len(filenames)
    i = 0
    for fn in filenames:
        if fn.lower().split('/')[-1].startswith('readme'):
            continue
        filtered_filenames += [fn]
        i += 1
        f=open('inaugural/'+fn)
        print 'Reading ' + f.name
        raw = f.read()
        tokens=nltk.word_tokenize(raw)
        # delete short words and make everything lowercase
        tokens=[w.lower() for w in tokens if len(w)>2]
        Speech_Length += [len(tokens)]
        Text.append(tokens)        
        Total=Total+tokens
    print '%s files were indexed (%s were ignored)' % (i, len(filenames)-i)
            
    Empirical_Total=nltk.FreqDist(Total)    
    Vocabulary=Empirical_Total.keys()   # the entire set of words
    Size=len(Vocabulary)
    #numDoc=len(Text)

    Dist=range(Size)
    Vectors=[]          # Record a list of empirical distributions
    for i in range(len(filenames)-1):
        fdist=nltk.FreqDist(Text[i])

        for j in range(Size):
            Dist[j]=fdist[Vocabulary[j]]
            
        Vectors.append(Dist[:]) # Dist[:] makes a copy of the list to append
    
    Word_Relevance=range(Size) # store a relevance score for each word
    for wordIndex in range(Size):
        Word_Dist= nltk.FreqDist([Vectors[i][wordIndex] for i in range(len(filenames)-1)])
        
        Word_Relevance[wordIndex]=0
        
        # # check if the number of files that do not have the word is close to half
        # if (abs(Word_Dist[0] - len(filenames)/2) <= 3):
        #    Word_Relevance[wordIndex]=1            
         
        # entropy normalized by the support 
        H_normalized = renyi_entropy(Word_Dist, alpha=.6, base=e, normalized=True)

        if (H_normalized > entropy_threshold):  # 0.9 is an arbitrary threshold
            Word_Relevance[wordIndex]=1
        
    Key_words= [Vocabulary[i] for i in range(Size) if Word_Relevance[i] !=0 ] 

    print 'Computed a relevance score for %s words and reduced it to %s words above %s%% relevance.' % (Size, len(Key_words), entropy_threshold)

    Reduced_Vectors=[]    
    for i in range(len(filenames)-1):
        Reduced_Vectors.append([Vectors[i][j] for j in range(Size) if Word_Relevance[j]!=0])
    
    U, s, V= np.linalg.svd(Reduced_Vectors)

    Scores=range(len(filenames)-1)
    print 'SCORES', ':', 'FILENAME'    
    for i in range(len(filenames)-1):
        Scores[i]= np.inner(V[0], Reduced_Vectors[i])/Speech_Length[i]
        print Scores[i], ':', filenames[i]
    return Scores, Reduced_Vectors, filtered_filenames, Key_words


def reverse_dict(d):
    return dict((v, k) for (k, v) in dict(d).iteritems())


def reverse_dict_of_lists(d):
    ans = {}
    for (k, v) in dict(d).iteritems():
        for new_k in list(v):
            ans[new_k] = k
    return ans


def shannon_entropy(discrete_distribution, base=e, normalized=True):
    """Shannon entropy (information uncertainty) for the logarithm base (units of measure) indicated

    The default logarithm base is 2, which provides entropy in units of bits. Shannon used
    bases of 2, 10, and e (natural log), but scipy and most math packages assume e.

    >>> from scipy.stats import entropy as scipy_entropy
    >>> scipy_entropy([.5, .5]) / log(2) # doctest: +ELLIPSIS
    1.0
    >>> shannon_entropy([.5, .5], base=2)
    0.69314718...
    >>> scipy_entropy([.5, .5])  # doctest: +ELLIPSIS
    0.69314718...
    1.0
    >>> shannon_entropy([.5, .5], base=2, normalized=False)  # doctest: +ELLIPSIS
    0.69314718...
    >>> scipy_entropy([c / 13. for c in [1, 2, 3, 4, 3]])  # doctest: +ELLIPSIS
    1.5247073930...
    >>> shannon_entropy([1, 2, 3, 4, 3], normalized=False)
    1.5247073930...
    """
    if isinstance(discrete_distribution, Mapping):
        discrete_distribution = discrete_distribution.values()
    if base == None:
        base = e

    if not len(discrete_distribution):
        raise RuntimeWarning("Empty discrete_distribution probability distribution, so Renyi entropy (information) is zero.")
        return float('-0.')
    if not any(discrete_distribution):
        raise RuntimeWarning("Invalid value encountered in divison, 0/0 (zero divided by zero). Sum of discrete_distribution (discrete distribution integral) is zero.")
        return float('nan')
    if any(count < 0 for count in discrete_distribution):
        raise RuntimeWarning("Some counts or frequencies (probabilities) in discrete_distribution were negative.")

    total_count = float(sum(discrete_distribution))

    if base == e:
        H = sum(count * log(count / total_count) for count in discrete_distribution) / total_count
    else:
        H = sum(count * log(count / total_count, base) for count in discrete_distribution) / total_count
    if normalized:
        return -1 * H / log(len(discrete_distribution), base)
    return -1 * H


def renyi_entropy(word_counts, alpha=1, base=2, normalized=True):
    """Renyi entropy of order alpha and the logarithm base (units of measure) indicated

    The default logarithm base is 2, which provides entropy in units of bits, Renyi's 
    preferred units. Shannon used bases of 2, 10, and e (natural log).

    >>> from scipy.stats import entropy as scipy_entropy
    >>> scipy_entropy([.4, .6])  # doctest: +ELLIPSIS
    0.97...
    >>> renyi_entropy([.4, .6])  # doctest: +ELLIPSIS
    0.97...
    >>> renyi_entropy([.4, .6], .6)
    0.97...
    >>> renyi_entropy([], .6)
    -0.0
    >>> renyi_entropy([0.] * 10, .6)
    nan
    """
    if isinstance(word_counts, Mapping):
        word_counts = word_counts.values()
    if base == None:
        base = e

    N = len(word_counts)
    if not N:
        raise RuntimeWarning("Empty word_counts probability distribution, so Renyi entropy (information) is zero.")
        return float('-0.')
    if not any(word_counts):
        raise RuntimeWarning("Invalid value encountered in divison, 0/0 (zero divided by zero). Sum of word_counts (discrete distribution integral) is zero.")
        return float('nan')

    if alpha == 1:
        return shannon_entropy(word_counts, base=base, normalized=normalized)

    total_count = float(sum(word_counts))    
    entropy_unif = log(N, base)  # log of the support, don't have to turn to float
    sum_pow = sum(pow(count / total_count, alpha) for count in word_counts)
    
    # log(x) is 75% faster as log(x, math.e), according to timeit on python 2.7.5
    # so split into 2 cases, base e (None), and any other base
    if base == e:
        log_sum_pow = log(sum_pow)
    else:
        log_sum_pow = log(sum_pow, base)

    H = log_sum_pow / (1 - alpha)

    if normalized:
        return H / (entropy_unif or 1.)
    else:
        return H


def zheng_normalized_entropy(Word_Dist, alpha=.6):
    """Renyi entropy of order alpha and the logarithm base (units of measure) indicated

    The default logarithm base is 2, which provides entropy in units of bits, Renyi's 
    preferred units. Shannon used bases of 2, 10, and e (natural log).

    >>> from scipy.stats import entropy as scipy_entropy
    >>> scipy_entropy([.4, .6])  # doctest: +ELLIPSIS
    0.97...
    >>> zheng_normalized_entropy([.4, .6], alpha=1)  # doctest: +ELLIPSIS
    0.97...
    >>> word_freq = [c / 13. for c in [1, 2, 3, 4, 3]]
    >>> zheng_normalized_entropy(dict((k, v) for (k, v) in enumerate(word_freq)))  # doctest: +ELLIPSIS
    0.966162932302...
    """
    keys=Word_Dist.keys()
    Entropy_Unif= log(len(keys))  # log of the support, don't have to turn to float
    totalcount= float(sum([Word_Dist[w] for w in keys]))
    
    Entropy= -sum([ Word_Dist[w]/totalcount * log(Word_Dist[w]/totalcount) for w in keys])
    
    # Renyi entropy of order alpha
    #Entropy = log(sum ([pow(float(Word_Dist[w])/totalcount, alpha) for w in keys]))/(1-alpha)

    return float(Entropy) / Entropy_Unif


def co_adjacency(adjacency_matrix, row_names, col_names=None, bypass_col_names=True):
    """Reduce a heterogenous adjacency matrix into a homogonous co-adjacency matrix

    coadjacency_matrix, names = co_adjacency(adjacency_matrix, row_names, col_names, bypass_col_names=True)
    """
    bypass_indx = int(not (int(bypass_col_names) % 2))
    names = (row_names, col_names or row_names)[bypass_indx]

    A = np.matrix(adjacency_matrix)
    if not bypass_indx:
        return (A * A.transpose()).tolist(), names
    return (A.transpose() * A).tolist(), names


def len_str_to_group(s, bin_min=None, bin_width=None):
    if bin_min is None:
        bin_min = len_str_to_group.min
    bin_width = bin_width or len_str_to_group.width or 1
    return int(round((len(s) - bin_min) / float(bin_width)))
len_str_to_group.min = 3
len_str_to_group.width = 3


def yr_str_to_group(s, bin_min=None, bin_width=None, digits=None):
    if bin_min is None:
        bin_min = yr_str_to_group.min
    if digits is None:
        digits = yr_str_to_group.digits
    bin_width = bin_width or yr_str_to_group.width or 1
    return int(round((float(s[:digits]) - bin_min) / float(bin_width)))
yr_str_to_group.min = 1770
yr_str_to_group.width = 3
yr_str_to_group.digits = 4


def scale_exp(value, in_min, in_max, out_min=1, out_max=10, exp=1):
    """Rescale a scalar value to fit within out_min and out_max

    >>> scale_exp(150, in_min=100, in_max=200, out_min=0, out_max=1)
    .5
    >>> scale_exp(150, in_min=100, in_max=200, out_min=0, out_max=1, exp=2)
    .25
    """
    return np.power((out_max - out_min) * (value - in_min) / float(in_max - in_min), exp)


def matrix_scale_exp(A, out_min=0, out_max=1, exp=1):
    """Apply scape_exp to all elements of a matrix, auto-calculating in_min and in_max
    """
    A = np.matrix(A)
    return scale_exp(A, np.min(A), np.max(A), out_min, out_max, exp=exp).tolist()


def strip_path_ext_characters(s, strip_characters=ascii.ascii_nonword):
    return str(s).split('/')[-1].split('.')[0].strip(strip_characters)


def d3_graph(adjacency_matrix, row_names, col_names=None, str_to_group=len_str_to_group, str_to_name=strip_path_ext_characters, str_to_value=float, num_groups=4.):
    """Convert an adjacency matrix to a dict of nodes and links for d3 graph rendering

    row_names = [("name1", group_num), ("name2", group_num), ...]
    col_names = [("name1", group_num), ("name2", group_num), ...]

    Usually row_names and col_names are the same, but not necessarily.
    Group numbers should be an integer between 1 and the number of groupings
    of the nodes that you want to display.

    adjacency_matrix = [
        [edge00_value, edge01_value, edge02_value...],
        [edge10_value, edge11_value, edge12_value...],
        [edge20_value, edge21_value, edge22_value...],
        ...
        ]

    The output is a dictionary of lists of vertexes (called "nodes" in d3)
    and edges (called "links" in d3):

    {
        "nodes": [{"group": 1, "name": "Alpha"}, 
                  {"group": 1, "name": "Beta"}, 
                  {"group": 2, "name": "Gamma"}, ...
                 ],
        "links": [{"source": 1, "target": 0, "value": 1}, 
                  {"source": 2, "target": 0, "value": 8}, 
                  {"source": 3, "target": 0, "value": 10}, 
                 ]
    }
    """
    if col_names is None:
        col_names = row_names

    nodes, links = [], []

    print '-' * 10
    # get the nodes list first, from the row and column labels, even if not square
    for names in (row_names, col_names):
        for i, name_group in enumerate(names):
            if isinstance(name_group, basestring):
                name_group = (str_to_name(name_group), str_to_group(name_group))
            node = {"name": name_group[0], "group": name_group[1] or 1}
            print node
            if node not in nodes:
                nodes += [node]

    # get the edges next
    for i, row in enumerate(adjacency_matrix):
        for j, value in enumerate(row):
            links += [{"source": i, "target": j, "value": str_to_value(value)}]

    return {'nodes': nodes, 'links': links}


def write_file_twice(js, fn, other_dir='../miner/static'):
    with open(fn, 'w') as f:
        json.dump(js, f, indent=2)
    other_path = os.path.join(other_dir, fn)
    if os.path.isdir(other_dir):
        with open(other_path, 'w') as f:
            json.dump(js, f, indent=2)


def president_party(name):
    surname = strip_path_ext_characters(name.split(' ')[-1], strip_characters=ascii.ascii_nonletter)
    return president_party.surname_party.get(surname, '')
president_party.party = reverse_dict_of_lists(json.load(open('data/president_political_parties.json','r')))
president_party.surname_party = dict((name.split(' ')[-1], party) for (name, party) in president_party.party.iteritems())


def party_to_group(s):
    return party_to_group.parties.get(s)
party_to_group.parties = dict((p, i + 1) for (i, p) in enumerate(json.load(open('data/president_political_parties.json','r'))))



if __name__ == '__main__':
    """
    # This will produce a 14 x 14 matrix, 
    >>> scores, adjacency_matrix, files, words = score_words_in_files(DEFAULT_FILE_LIST[:14], entropy_threshold=0.99)
    >>> coadjacency, names = co_adjacency(adjacency_matrix, row_names=files, col_names=words, bypass_col_names=True)
    """
    num_groups = 3.
    scores, adjacency_matrix, files, words = score_words_in_files(sorted(DEFAULT_FILE_LIST), entropy_threshold=0.92)

    O, names = co_adjacency(adjacency_matrix, row_names=files, col_names=words, bypass_col_names=False)
    O = matrix_scale_exp(O, out_min=1 ** 2, out_max=31 ** 2, exp=.5)
    len_str_to_group.min = min(len(s) for s in names)
    len_str_to_group.width = (max(len(s) for s in names) - len_str_to_group.min) / num_groups
    graph = d3_graph(O, names, str_to_group=len_str_to_group)
    write_file_twice(graph, 'word_coocurrence.json')
   
    print files
    print words


    O, names = co_adjacency(adjacency_matrix, row_names=files, col_names=words, bypass_col_names=True)
    print names, len(O), len(O[0])
    O = matrix_scale_exp(O, out_min=1 ** .66, out_max=31 ** .66, exp=1.5)
    yr_str_to_group.digits = 4
    yr_str_to_group.min = min(float(s[:4]) for s in names)
    yr_str_to_group.width = (max(float(s[:4]) for s in names) - yr_str_to_group.min) / num_groups
    graph = d3_graph(O, [(strip_path_ext_characters(n), party_to_group(president_party(n))) for n in names], str_to_group=yr_str_to_group)
    write_file_twice(graph, 'doc_coocurrence.json')
