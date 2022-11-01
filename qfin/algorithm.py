from tqdm import tqdm
from .stockdata import StockData
'''
TODO: This class should definitely contain information about "add_indicator" as 
they are part of the strategy...
'''


class Algorithm:

    def __init__(self):
        self._stocks = None
        self._indicator_funcs = dict()
        self._cash = None
        self._fee = None
        self.stocks = None

    @property
    def cash(self):
        return self._cash

    @cash.setter
    def cash(self, cash):
        # TODO: add inputting checks
        self._cash = cash

    @property
    def fee(self):
        return self._fee

    @fee.setter
    def fee(self, fee):
        # TODO: add inputting checks
        self._fee = fee

    def update_prices(self, prices):
        self._prices = prices

    def add_indicator(self, name, func):
        if not callable(func):
            raise ValueError(
                f'add_indicator expects a function, not {type(func)}')

        self._indicator_funcs[name] = func

    @property
    def indicator_functions(self):
        return self._indicator_funcs
    
    def run_on_data(self, curr_prices, data):
        self._prices = curr_prices
        self.on_data(data)

    # to override
    def on_data(self, data: dict):
        pass

class Position:
    def __init__(self, price, quantity):
        self._price = price
        self._quantity = quantity

    
        