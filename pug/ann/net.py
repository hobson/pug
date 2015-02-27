class NeuralNet(object):
    
    def __init__(W=None):
        if isinstance(W, (tuple, list, np.ndarray, np.array)):
            if isinstance(W[0], int):
                N_in = W[0]
                N_out = W[-1]
            else:
                N_in = len(W[0][0])
                N_out = len(W[-1][0])
                self.Ws = list(np.matrix(W) for W in Ws)