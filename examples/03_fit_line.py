"""This example demonstrates how to use ``speval`` to find optimal line through
a given data via grid search or random search.
"""
import argparse
import logging

import numpy as np
from speval import speval

logging.basicConfig(level = logging.INFO)

parser = argparse.ArgumentParser("Linear regression")
parser.add_argument(
    'method', metavar = 'METHOD', type = str, choices = [ 'rand', 'grid' ],
    nargs = '?', default = 'rand', help = 'Search Method'
)

def construct_search_space(n, method):

    if method == 'grid':
        return [
            {'a' : a, 'b' : b} \
                for a in np.linspace(0, 1000, n) \
                for b in np.linspace(0, 1000, n)
        ]

    else:
        np.random.seed(12345)

        return [
            {'a' : a, 'b' : b} \
                for (a,b) in np.random.uniform(
                    low = -1000, high = 1000, size = (n * n, 2)
                )
        ]

def linear_func(x, a, b):
    return a * x + b

def objective_function(x, y_true, a, b):
    y_pred = linear_func(x, a, b)
    return np.average((y_true - y_pred)**2)


args = parser.parse_args()

x      = np.linspace(-100, 100, 10000)
y_true = linear_func(x, 123, 456)

n = 30

eval_space = construct_search_space(n, args.method)

speval(
    lambda kwargs : objective_function(x, y_true, **kwargs),
    eval_space,
    "/tmp/03_fit_line_%s.db" % (args.method),
    timeout = 60
)

