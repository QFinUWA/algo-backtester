from tqdm import tqdm
from .stockdata import StockData
from ._portfolio import Portfolio

'''
TODO: This class should definitely contain information about "add_indicator" as 
they are part of the strategy...
'''


class Algorithm:

    def __init__(self):
        self._stocks = None
        self._indicator_funcs = dict()

    @property
    def indicator_functions(self):
        return self._indicator_funcs

    def add_indicator(self, name, func):
        if not callable(func):
            raise ValueError(
                f'add_indicator expects a function, not {type(func)}')

        self._indicator_funcs[name] = func
    
    def run_on_data(self, curr_prices, data, portfolio):
        portfolio.curr_prices = curr_prices
        self.on_data(data, portfolio)

    # to override
    def on_data(self, data: dict, portfolio: Portfolio):
        pass

    
        