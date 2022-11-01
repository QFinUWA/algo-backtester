
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

    def add_indicator(self, name, func):
        if not callable(func):
            raise ValueError(
                f'add_indicator expects a function, not {type(func)}')

        self._indicator_funcs[name] = func

    @property
    def indicator_functions(self):
        return self._indicator_funcs

    # to override
    def on_data(self, data: dict):
        pass
