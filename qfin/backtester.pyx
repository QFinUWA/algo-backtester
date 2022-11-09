from cybacktester cimport CythonBacktester
from cyalgorithm cimport CythonAlgorithm

from functools import wraps


def indicator(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):
        func(*args, **kwargs)
    wrapper_func.indicator = True
    return wrapper_func


class Backtester(CythonBacktester):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Algorithm(CythonAlgorithm):

    def __init__(self):
        super().__init__()

