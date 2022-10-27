import pandas as pd

import numpy as np


class Backtester:

    def __init__(self):

        self._init_data = pd.read_csv('apple.csv', index_col=0)

        self._i = 0

    @property
    def df(self):
        return self._init_data

    @property
    def price(self):
        return self._init_data['price']

    @property
    def volume(self):
        return self._init_data['volume']

    def add_indicator(self, name, func):

        if not callable(func):
            raise ValueError(
                f'add_indicator expects a function, not {type(func)}')

        # if function is passed
        if callable(func):
            self._init_data[name] = func(self._init_data)
            return

    def add_indicators(self, table):

        # TODO check that this works
        if not any(type(name) is str and callable(func) for name, func in table.items()):
            raise ValueError(
                f'add_indicator expects a dictionary mapping str to func, not {type(name)} to {type(func)}.')

        for name, func in table.items():
            self.add_indicator(name, func)
