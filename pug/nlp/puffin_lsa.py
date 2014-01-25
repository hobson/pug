"""
from PuffineWareLLC.com whitepaper on LSA -- Puffinware makes a Windows Search tool
"""
from scipy.linalg import svd
#following needed for TFIDF
from math import log
import numpy as np


class PuffinLSA(object):

    def __init__(self, ignore_words=None, ignore_chars=None):
        self.ignore_words = ['and', 'or', 'for', 'in', 'on', 'of', 'near', 'to', 'a'] if ignore_words is None else ignore_words
        self.ignore_chars = r",:'!" if ignore_chars is None else ignore_chars
        self.wdict = {}
        self.keys = self.A = self.U = self.S = self.Vt = None
        self.dcount = 0        

    def parse(self, doc):
        words = doc.split()
        for w in words:
            w = w.lower().translate(None, self.ignore_chars)
            if w in self.ignore_words:
                continue
            elif w in self.wdict:
                self.wdict[w].append(self.dcount)
            else:
                self.wdict[w] = [self.dcount]
        self.dcount += 1      

    def build(self):
        self.keys = [k for k in self.wdict.keys() if len(self.wdict[k]) > 1]
        self.keys.sort()
        self.A = np.zeros([len(self.keys), self.dcount])
        for i, k in enumerate(self.keys):
            for d in self.wdict[k]:
                self.A[i,d] += 1

    def calc(self):
        self.U, self.S, self.Vt = svd(self.A)

    def TFIDF(self):
        WordsPerDoc = np.sum(self.A, axis=0)        
        DocsPerWord = np.sum(np.asarray(self.A > 0, 'i'), axis=1)
        rows, cols = self.A.shape
        for i in range(rows):
            for j in range(cols):
                self.A[i,j] = (self.A[i,j] / WordsPerDoc[j]) * log(float(cols) / DocsPerWord[i])

    def printA(self):
        print 'Here is the count matrix'
        print self.A

    def printSVD(self):
        print 'Here are the singular values'
        print self.S
        print 'Here are the first 3 columns of the U matrix'
        print -1*self.U[:, 0:3]
        print 'Here are the first 3 rows of the Vt matrix'
        print -1*self.Vt[0:3, :]

