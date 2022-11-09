from tqdm import tqdm
from opt.stockdata cimport StockData
from opt.portfolio cimport Portfolio
import inspect 

cdef class CythonAlgorithm:

    def __init__(self):
        self.indicator_parameters = dict()

    @property
    def indicator_functions(self):
        # TODO: filter by only functions
        return {k:v for k, v in inspect.getmembers(type(self)) 
                if callable(v) and hasattr(getattr(self, k), 'indicator') and not k.startswith('__')}

#    def add_indicator(self, name, func):
#        if not callable(func):
#            raise ValueError(
#                f'add_indicator expects a function, not {type(func)}')
#
#        self._indicator_funcs[name] = func

    def run_on_data(self, curr_prices, data, portfolio):
        portfolio.curr_prices = curr_prices
        self.on_data(data, portfolio)

    # to override
    def on_data(self, data: dict, portfolio):
        return
