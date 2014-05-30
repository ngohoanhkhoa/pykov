import numpy
from utils import * 

INITIALIZATION_MODE = "random"
MAX_ITERS = 1000
CONV_CRIT = 0.00001

def baum_welch(observations, N, M):
    """
    N is the number of hidden states, M is the number of different possible observations
    """
    T = observations.shape[0]

    # initialize variables
    pi, A, B = initialize_variables(N, M, mode=INITIALIZATION_MODE)

    likelihoods = numpy.zeros(MAX_ITERS + 1)

    # go to log-space
    pi = numpy.log(pi)
    A = numpy.log(A)
    B = numpy.log(B)
    print 'initialization: Done'

    converge = False

    iter_num = 0
    while not converge:
        likelihoods[iter_num] = calculate_likelihood(observations, pi, A, B)
        iter_num += 1

        # iterate
        new_pi, new_A, new_B = EM_iterate(observations, N, M, T, pi, A, B)
        print 'EM Iteration: %d' % iter_num

        # check convergence
        converge = did_converge(pi, A, B, new_pi, new_A, new_B)
        if iter_num > MAX_ITERS:
            converge = True

        #update values
        pi, A, B = new_pi, new_A, new_B
    # return variables
    return pi, A, B, likelihoods

def EM_iterate(observations, N, M, T, pi, A, B):
    """ Expectation """
    alphas = forward_path(observations, pi, A, B, T, N)
    betas = backward_path(observations, pi, A, B, T, N)

    gammas = calculate_gammas(alphas, betas, T, N)
    kesies = calculate_ksies(observations, alphas, betas, A, B, T, N)

    """ Maximization """
    new_pi = gammas[0, :]

    new_A = numpy.zeros((N, N))
    for i in range(N):
        norm_factor = add_logs(gammas[:-1, i])
        for j in range(N):
            new_A[i, j] = add_logs(kesies[:-1, i, j]) - norm_factor

    new_B = numpy.zeros((N, M))
    for i in range(N):
        norm_factor = add_logs(gammas[:, i])
        for k in range(M):
            new_B[i, k] = add_logs(gammas[:, i][observations == k]) - norm_factor

    return new_pi, new_A, new_B

def did_converge(pi, A, B, new_pi, new_A, new_B):
    if numpy.linalg.norm(pi - new_pi) > CONV_CRIT:
        return False
    if numpy.linalg.norm(A - new_A) > CONV_CRIT:
        return False
    if numpy.linalg.norm(B - new_B) > CONV_CRIT:
        return False
    return True

def initialize_variables(N, M, mode="random"):
    """
    initializes the model parameters
    It can perform in two modes, "random", "equal"
    """
    A = numpy.zeros((N, N))
    B = numpy.zeros((N, M))
    pi = numpy.zeros(N)

    if mode == "random":
        pi = numpy.random.random(N)
        pi = pi / pi.sum()

        for i in range(N):
            tempA = numpy.random.random(N)
            A[i, :] = tempA / tempA.sum()

            tempB = numpy.random.random(M)
            B[i, :] = tempB / tempB.sum()
    elif mode == "equal":
        pi[:] = 1. / N
        A[:] = 1. / N
        B[:] = 1. / M
    else:
        raise Exception("invalid mode: %s" % mode)

    return pi, A, B

def calculate_gammas(alphas, betas, T, N):
    gammas = numpy.zeros((T, N))

    for t in range(T):
        for i in range(N):
            gammas[t, i] = alphas[t, i] + betas[t, i]
        sum_all = add_logs(gammas[t, :])
        gammas[t, :] = gammas[t, :] - sum_all

    return gammas

def calculate_ksies(observations, alphas, betas, A, B, T, N):
    ksies = numpy.zeros((T, N, N))

    norms = numpy.zeros(T)

    for t in range(T):
        temps = numpy.zeros(N)
        for k in range(N):
            temps[k] = alphas[t, k] + betas[t, k]
        norms[t] = add_logs(temps)

    for t in range(T-1):
        for i in range(N):
            for j in range(N):
                ksies[t, i, j] = alphas[t, i] + A[i, j] + betas[t+1, j] + B[j, observations[t+1]] - norms[t]

    return ksies