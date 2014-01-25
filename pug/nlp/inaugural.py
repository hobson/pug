# -*- coding: utf-8 -*-

import os
import nltk
import numpy
import math

if(__name__=="__main__"):

    filenames = os.listdir('inaugural')

    Text=[]     # list of tokened texts
    Total=[]    # all texts put together 
    Speech_Length= range(len(filenames)-1)
    
    for i in range(len(filenames)-1):
        f=open('inaugural/'+filenames[i])
        raw = f.read()
        tokens=nltk.word_tokenize(raw)
        # delete short words and make everything lowercase
        tokens=[w.lower() for w in tokens if len(w)>2]
        Speech_Length[i]=len(tokens)
        Text.append(tokens)        
        Total=Total+tokens
            
    Empirical_Total=nltk.FreqDist(Total)    
    Vocabulary=Empirical_Total.keys()   # the entire set of words
    Size=len(Vocabulary)
    numDoc=len(Text)

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
        if (Entropy_Normalized > 0.9):  # 0.9 is an arbitrary threshold
            Word_Relevance[wordIndex]=1
        
    Key_words= [Vocabulary[i] for i in range(Size) if Word_Relevance[i] !=0 ] 
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
    print filenames