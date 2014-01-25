# -*- coding: utf-8 -*-

import os
import nltk
import numpy
import math

DEFAULT_FILE_LIST = os.listdir('inaugural')

def main(filenames=DEFAULT_FILE_LIST, entropy_threshold=0.9):

    filenames = os.listdir('inaugural')

    Text = []     # list of tokened texts
    Total = []    # all texts put together 
    Speech_Length = []
    
    print 'Reading %s files' % len(filenames)
    i = 0
    for fn in filenames:
        if fn.lower().split('/')[-1].startswith('readme'):
            continue
        i += 1
        f=open('inaugural/'+filenames[i])
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
    
        keys=Word_Dist.keys()
        Entropy_Unif= math.log(len(keys))  # log of the support, don't have to turn to float
        totalcount= float(sum([Word_Dist[w] for w in keys]))
        
        #Entropy= -sum([ Word_Dist[w]/totalcount * math.log(Word_Dist[w]/totalcount) for w in keys])
        
        # Renyi entropy of order alpha

        alpha=0.6
        
        Entropy = math.log(sum ([pow(Word_Dist[w]/totalcount, alpha) for w in keys]))/(1-alpha)
                        
        Entropy_Normalized= Entropy/Entropy_Unif
        if (Entropy_Normalized > entropy_threshold):  # 0.9 is an arbitrary threshold
            Word_Relevance[wordIndex]=1
        
    Key_words= [Vocabulary[i] for i in range(Size) if Word_Relevance[i] !=0 ] 

    print 'Computed a relevance score for %s words and reduced it to %s words above %s%% relevance.' % (Size, len(Key_words), entropy_threshold)

    Reduced_Vectors=[]    
    for i in range(len(filenames)-1):
        Reduced_Vectors.append([Vectors[i][j] for j in range(Size) if Word_Relevance[j]!=0])
    
    U,s,V= numpy.linalg.svd(Reduced_Vectors)

    Scores=range(len(filenames)-1)    
    for i in range(len(filenames)-1):
        Scores[i]= numpy.inner(V[0], Reduced_Vectors[i])/Speech_Length[i]
        print filenames[i]        
        print Scores[i]
        print '\n'
    return Scores, Reduced_Vectors, filenames, Key_words


def d3_graph(adjacency_matrix, row_names, col_names=None):
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

    # get the nodes list first, from the row and column labels, even if not square
    for names in (row_names, col_names):
        for i, name in enumerate(names):
            node = {"name": str(name[0]), "group": int(name[1]) or 1}
            if node not in nodes:
                nodes += [node]

    # get the edges next
    for i, row in enumerate(adjacency_matrix):
        for j, value in enumerate(row):
            links += [{"source": 0, "target": 1, "value": int(value)}]

    return {'nodes': nodes, 'links': links}


def co_adjacency(adjacency_matrix, row_names, col_names=None, bypass_col_names=True):
    for i, row in enumerate(adjacency_matrix):
        for j, value in row:
            pass

            
        

if __name__ == '__main__':
    print main()
