import sys, pickle, numpy
import matplotlib.pyplot as pyplot
zeros = numpy.zeros
ones = numpy.ones
rand = numpy.random.rand


# This function returns a projection vector for binary decision. p_matrix is a n_training x n_dimensions
# numpy array with the positions achieved from the spring function. label is a n_training x 1 numpy array
# of +/-1 labels.
def projection_vector(p_matrix, label):
  assert p_matrix.shape[0] == label.shape[0]
  temp = numpy.copy(p_matrix)
  for idx in range(p_matrix.shape[0]):
    temp[idx][:] = label[idx]*temp[idx][:]
  unnormalized_pv = temp.sum(axis = 0)
  return unnormalized_pv/pow(numpy.dot(unnormalized_pv, unnormalized_pv.T), 0.5)
  

# This function returns the final position matrix. d_matrix is a n_training x n_training numpy array
# with all the pairwise distances. Drift is a function that uses labels to vary the drift between each
# iteration. label is a n_training x 1 numpy array of +/-1 labels.
def spring(d_matrix, drift, label, n_dimensions, n_iteration):
  # Make sure distance matrix is square.
  assert d_matrix.shape[0] == d_matrix.shape[1]
  n_elements = d_matrix.shape[0]
  p_matrix = init_position(d_matrix, n_dimensions)
  
  for idx in range(n_iteration):
    # Perform drift based on the function provided.
    # Perform spring based iterative positioning. We hope this will converge
    # to our desired distance matrix.
    p_matrix = p_matrix + drift(label, n_dimensions)
    p_matrix = propagate(p_matrix, d_matrix)
  
  # Accumulate the squared error for every pairwise distance. 
  mse = [0, 0]
  for actor in range(d_matrix.shape[0]):
    for acted in range(d_matrix.shape[0]):
      if actor != acted:
        #import pdb
        #pdb.set_trace()
        mse[0] += pow(d_matrix[actor][acted]-distance(p_matrix[actor][:], p_matrix[acted][:]), 2)
        mse[1] += 1
  print mse
  return p_matrix
  

# Randomly initialize position.
def init_position(d_matrix, n_dimensions):
  n_elements = d_matrix.shape[0]
  return rand(n_elements, n_dimensions)
  
def drift(label, n_dimensions):
  p_change = 0.01*ones(shape = (label.shape[0], n_dimensions))
  for idx in range(p_change.shape[0]):
    if label[idx] < 0:
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
  
  
  temp = 2*rand(6, 6)
  label = 2*(numpy.random.randint(0, 2, (6, 1))-0.5)
  p_matrix = spring(temp.T+temp, drift, label, 5, 555)
  
  
  
  #temp = numpy.array([[0, 0.1, 1, 1.1], [0, 0, 1.2, 1.4], [0, 0, 0, 0.05], [0, 0, 0, 0]])
  #label = numpy.array([[1], [1], [-1], [-1]])
  #p_matrix = spring(temp.T+temp, drift, numpy.array([[1], [1], [-1], [-1]]), 2, 555)

  # Center the positions.
  p_mean = p_matrix.mean(0)
  for idx in range(p_matrix.shape[0]):
    p_matrix[idx][:] = p_matrix[idx][:]-p_mean
  
  # Find the projection vector and plot the training data.
  a = projection_vector(p_matrix, label)
  fig = pyplot.figure()
  
  for idx in range(p_matrix.shape[0]):
    if label[idx] >= 0:
      pyplot.scatter(p_matrix[idx][0], p_matrix[idx][1], s=100, c='r')
    else:
      pyplot.scatter(p_matrix[idx][0], p_matrix[idx][1], s=100, c='b')
  ax = pyplot.axes()
  ax.arrow(0, 0, a[0], a[1], head_width=0.05, head_length=0.1, fc='k', ec='k')
  pyplot.axis([-3, 3, -3, 3])
  pyplot.show()
  
if __name__ == '__main__':
  main()