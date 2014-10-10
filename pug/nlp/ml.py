# HL: unused
# import sys, pickle

import numpy

import matplotlib.pyplot as pyplot

zeros = numpy.zeros

ones = numpy.ones

rand = numpy.random.rand





# This function returns a projection vector for binary decision. p_matrix is a n_training x n_dimensions

# numpy array with the positions achieved from the spring function. labels is a n_training x 1 numpy array

# of +/-1 labels.

def projection_vector(p_matrix, labels):

  assert p_matrix.shape[0] == labels.shape[0]

  temp = numpy.copy(p_matrix)

  for idx in range(p_matrix.shape[0]):

    temp[idx][:] = labels[idx]*temp[idx][:]

  unnormalized_pv = temp.sum(axis = 0)

  return unnormalized_pv/pow(numpy.dot(unnormalized_pv, unnormalized_pv.T), 0.5)

  

# MAIN function

# This function returns the final position matrix. d_matrix is a n_training x n_training numpy array

# with all the pairwise distances. Drift is a function that uses labels to vary the drift between each

# iteration. labels is a n_training x 1 numpy array of +/-1 labels.

# which direction is steepest in your training data
# average of blue points and red points, the vectors between the groups to say which group the node is closer too

def spring(d_matrix, drift, labels, n_dimensions=5, n_iteration=555):
  """Propagate the p_matrix (positions of the nodes) for n_iterations printing out the MSE matrix at the end.
      
    Returns:
      p_matrix (np.matrix of float): each row is a node position?  the eigenvectors of the reduced dimensional space?

    Arguments:
      d_matrix (np.matrix of float): symmetric N x N matrix of distances between nodes (documents)
        column is node called `acted` the one being pulled, the column the node doing the push/pulling `actor`
      drift (bool): whether there should be some supervisory force to keep the absolute position of nodes near zero
      labels (list of int): +/- 1 for each of N nodes or 0 if no labeled. +/-1 for only 2 categories or labels in your training set
      n_dimensions (int): number of dimensions to reduce to
        We don't know how many dimensions our final vector will be, so adjust this from low to high until the gain in mse is small
      n_iterations (int): number of times
  """
  # Make sure distance matrix is square.

  assert d_matrix.shape[0] == d_matrix.shape[1]

  # # HL: FIXME: delete this unused variable
  # n_elements = d_matrix.shape[0]

  p_matrix = init_position(d_matrix, n_dimensions)


  for idx in range(n_iteration):

    # Perform drift based on the function provided.

    # Perform spring based iterative positioning. We hope this will converge

    # to our desired distance matrix.

    p_matrix = p_matrix + drift(labels, n_dimensions)

    p_matrix = propagate(p_matrix, d_matrix)

  

  # Accumulate the squared error for every pairwise distance. 

  # propogate all the forces to all the nodes for one time step
  mse = [0, 0]

  for actor in range(d_matrix.shape[0]):

    for acted in range(d_matrix.shape[0]):

      if actor != acted:

        #import pdb

        #pdb.set_trace()

        #           
        # LZ:          spring rest-length      actual distance(N-dim vector, N-dim vect)        
        mse[0] += pow(d_matrix[actor][acted]-distance(p_matrix[actor][:], p_matrix[acted][:]), 2)

        mse[1] += 1

  print mse

  return p_matrix

  



# Randomly initialize position.

def init_position(d_matrix, n_dimensions):

  n_elements = d_matrix.shape[0]

  return rand(n_elements, n_dimensions)

  

def drift(labels, n_dimensions):

  p_change = 0.01*ones(shape = (labels.shape[0], n_dimensions))

  for idx in range(p_change.shape[0]):

    if labels[idx] < 0:

      p_change[idx][:] = -p_change[idx][:]

  return p_change





def propagate(p_matrix, d_matrix):

  spring_constant = 0.1

  f_matrix = zeros(shape = p_matrix.shape)

  for acted in range(d_matrix.shape[0]):

    for actor in range(d_matrix.shape[0]):

      if acted != actor:

        #import pdb

        #pdb.set_trace()
        # LZ: force vector in N-dim                     desired distance(N-dim vector, N-dim vect)    actual distance
        f_matrix[acted][:] += -spring_constant*(distance(p_matrix[actor][:], p_matrix[acted][:])-d_matrix[actor][acted])*(p_matrix[acted][:]-p_matrix[actor][:])/distance(p_matrix[actor][:], p_matrix[acted][:])
        
  return p_matrix + f_matrix



  

# Implements dot product.

def distance(x, y):

  temp = (x - y).T

  return pow(numpy.dot(temp.T, temp), 0.5)


def outcome_map1(outcome):

  if outcome == 'PART':

    return 1

  else:

    return -1





def main():
  """Attempt to find the optimal clusters and dimensions for a set of documents

  To create a test distance matrix with say 100 documents just:
    1. create 100 1000-D points (high dimension) that are Gaussian iid
    2. move half (50) of the points some significant distance from the others to create 2 groups/clusters
    3. calculate the distance between all the documents to populate the 100x100 distance matrix

  * Run this distance matrix through the algorithm (propagate) as if it was the Natural language distance
  * The data should stop improving the mse at about 12 dimensions (for LiZhong's tests)
  
  Note:
    * It may not work well on our low dimensional, low information-content (short with lots of repetition of phrases) "documents"
  """

  #args = sys.argv[1:]

  #pickle_name = args[0]

  #with open(pickle_name) as f:

  #  database, diagnosis, outcome = pickle.load(f)

  #

  #for idx in range(len(outcome)):

  #  outcome[idx] = outcome_map1(outcome[idx])

  #with open("result.txt", 'w') as f:

  #  for database_idx in range(len(database)):

  #    counter_T = 0

  #    counter_F = 0

  #    for diagnosis_idx in range(len(diagnosis)):

  #      if diagnosis[diagnosis_idx] == database_idx:

  #        if outcome[diagnosis_idx] == 1:

  #          counter_T += 1

  #        else:

  #          counter_F += 1

  #    f.write(str(database_idx) + ' ' + database[database_idx] + ',    ' + str(counter_T) + ',' + str(counter_F) + '\n')

  

  
  # HL: random 6x6 matrix
  temp = 2*rand(6, 6)

  # HL: random labels +/- 1
  labels = 2*(numpy.random.randint(0, 2, (6, 1))-0.5)

  # HL: this is the "Main" work that shold take a while on a big matrix
  p_matrix = spring(temp.T+temp, drift, labels, 5, 555)

  


  

  #temp = numpy.array([[0, 0.1, 1, 1.1], [0, 0, 1.2, 1.4], [0, 0, 0, 0.05], [0, 0, 0, 0]])

  #labels = numpy.array([[1], [1], [-1], [-1]])

  #p_matrix = spring(temp.T+temp, drift, numpy.array([[1], [1], [-1], [-1]]), 2, 555)



  # Center the positions.

  p_mean = p_matrix.mean(0)

  for idx in range(p_matrix.shape[0]):

    p_matrix[idx][:] = p_matrix[idx][:]-p_mean

  

  # Find the projection vector and plot the training data.
  a = projection_vector(p_matrix, labels)

  pyplot.figure()

  for idx in range(p_matrix.shape[0]):

    if labels[idx] >= 0:

      pyplot.scatter(p_matrix[idx][0], p_matrix[idx][1], s=100, c='r')

    else:

      pyplot.scatter(p_matrix[idx][0], p_matrix[idx][1], s=100, c='b')

  ax = pyplot.axes()

  ax.arrow(0, 0, a[0], a[1], head_width=0.05, head_length=0.1, fc='k', ec='k')

  pyplot.axis([-3, 3, -3, 3])

  pyplot.show()

  

if __name__ == '__main__':

  main()
