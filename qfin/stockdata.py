import numpy as np
import pandas as pd


class StockData:

    def __init__(self, frequency='15mins', stocks=['apple', 'google'], period='2022-2023'):
        self._stocks = stocks
        self._indicators = ['price', 'volume']
        self._i = 0
        self._data = {stock: None for stock in stocks}

        self._stock_df = dict()
        # TODO CLEAN THIS
        self._L = len(pd.read_csv(f'apple.csv', index_col=0))
        for stock in stocks:
            self._stock_df[stock] = pd.read_csv(f'apple.csv', index_col=0)

        self._update_data()


    def __len__(self):
        return self._L


    def __iter__(self):
        self._i = 0
        return self

    def __next__(self):
        self._i += 1
        # print('\t', self._i)
        if self._i == self._L + 1:
            raise StopIteration
        return {stock: self._data[stock][:self._i] for stock in self._stocks}

    @property
    def stocks(self):
        return stocks

    def _update_data(self):
        for stock in self._stocks:
            self._data[stock] = self._stock_df[stock].to_numpy()

    def add_indicator(self, name, func, update=True):
        self._indicators.append(name)
        if not callable(func):
            raise ValueError(
                f'add_indicator expects a function, not {type(func)}')

        # if function is passed
        for stock, df in self._stock_df.items():
            if callable(func):
                # print(df.head(10))
                self._stock_df[stock][name] = func(df)

        if update:
            self._update_data()

    def add_indicators(self, table):

        # TODO check that this works
        if not any(type(name) is str and callable(func) for name, func in table.items()):
            raise ValueError(
                f'add_indicator expects a dictionary mapping str to func, not {type(name)} to {type(func)}.')

        for name, func in table.items():
            self.add_indicator(name, func, update=False)
        self._update_data()
