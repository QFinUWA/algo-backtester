from cybacktester cimport CythonBacktester
from cyalgorithm cimport CythonAlgorithm

from functools import wraps


class Backtester(CythonBacktester):
    def __init__(self, algorithm, stocks, **kwargs):
        super().__init__(algorithm, stocks, **kwargs)


class Algorithm(CythonAlgorithm):

    def __init__(self):
        super().__init__()

    @classmethod
    def indicator(cls, func, *args, **kwargs):
        @wraps(func)
        def wrapper_func(*_args, **_kwargs):
            return func(*_args, **_kwargs)
        wrapper_func.indicator = True
        return wrapper_func
