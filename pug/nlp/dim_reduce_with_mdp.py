import mdp
import numpy as np
import scipy
import inaugural as data

occurrences, row_labels, col_labels = data.get_adjacency_matrix(sorted(data.DEFAULT_FILE_LIST), entropy_threshold=0.1, normalized=False, verbosity=1)
def reduce(occurrences=occurrences, dim=2):
    pca = mdp.nodes.PCANode(output_dim=dim, dtype='float64')
A = scipy.sparse.csr_matrix(A)
A.size
len(A.A)
len(A.A[0])
A.dtype
A = scipy.sparse.csr_matrix(A, dtype='float64')
A.A.nbytes
2500 * 56 * 8
pcanode80d = mdp.nodes.PCANode(output_dim=.8, dtype='float64')
pcanode80d.train(A)
pcanode80d.train(A.A)
pcanode80d.stop_training()
pcanode80d.avg
pca = pcanode80d
del(pcanode80d)
pca.d
pca.explained_variance
pca.get_current_train_phase
pca.get_current_train_phase()
pca.output_dim
pca.input_dim
pca.is_invertible
pca.is_invertible()
pca.has_multiple_training_phases
pca.has_multiple_training_phases()
pca.save
pca.save('pca.pickled')
pca.svd
pca.v
pca.var_abs
pca.var_part
pca.var_rel
pca.tlen
# pca.svg??
pca.svg
pca.svd
# pca.svd??
len(pca.v)
len(words_
)
len(words
)
words[pca.v.index(max(pca.v))]
max(pca.v)
words[np.where(pca.v==max(pca.v))]
words[np.where(pca.v==max(pca.v))[0]]
words
for var in pca.v:
    if var[0] > .8:
        print var[0], words[i]
for i, var in enumerate(pca.v):
    if var[0] > .8:
        print var[0], words[i]
for i, var in enumerate(pca.v):
    if var[0] > .7:
        print var[0], words[i]
for i, var in enumerate(pca.v):
    if var[0] > .5:
        print var[0], words[i]
for i, var in enumerate(pca.v):
    if var[0] > .3:
        print var[0], words[i]
for i, var in enumerate(pca.v):
    if var[0] > .2:
        print var[0], words[i]
for i, var in enumerate(pca.v):
    if var[0] > .1:
        print var[0], words[i]
for i, var in enumerate(pca.v):
    if var[0] > .05:
        print var[0], words[i]
word_var = []
for i, var in enumerate(pca.v):
    word_var += [(var[0], words[i])]
sorted(word_var)[:50]
sorted(word_var, reverse=True)[:50]
history
