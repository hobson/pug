import pug.nlp.inaugural as nlp
from tabulate import tabulate
import numpy as np

# duplicates results of tutorial at http://webhome.cs.uvic.ca/~thomo/svd.pdf

# changed died to die and new-hampshire to hampshire to avoid stemming
data = [
    'Romeo and Juliet.',
    'Juliet: O happy dagger!',
    'Romeo die by dagger.',
    '"Live free or die”, that’s the Hampshire’s motto.',
    'Did you know, New-Hampshire is in New-England.',
    ]


O, row_labels, col_labels = nlp.get_occurrence_matrix(data)
O = np.matrix(O).transpose().tolist()
row_labels, col_labels = col_labels, row_labels

keywords = ('romeo', 'juliet', 'happy', 'dagger', 'live', 'die', 'free', 'hampshire')
O_small = [O[row_labels.index(kw)] for kw in keywords if kw in row_labels]

print '\n'.join(keywords)
print tabulate(O_small, [str(cl) for cl in col_labels])

U, s, V = np.linalg.svd(O_small, full_matrices=False)
Sigma = np.diag(s)

np.allclose(O_small, np.dot(U,np.dot(Sigma, V)))

# reduced number of dimensions
k = 2
S_k = np.diag(s[:k])
U_k = np.array([U[i][:k] for i in range(U.shape[0])])
V_k = np.array([V[i] for i in range(k)])

O_k = np.dot(U_k, np.dot(S_k, V_k))

print keywords
print tabulate(S_k)
print tabulate(U_k)
print tabulate(V_k)