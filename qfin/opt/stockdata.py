import numpy as np
import pandas as pd
import os
from itertools import product


class StockData:

    def __init__(self, stocks, data_folder):

        self._indicators = ['open', 'close', 'high', 'low', 'volume']
        self._i = 0

        self._stock_df = dict()

        if len(stocks) == 0:
            raise ValueError(
                f'Please provide a list of stocks.')

        self._L = 0
        for stock in stocks:

            _df = pd.read_csv(os.path.join(data_folder, f'{stock}.csv'))
            _df = _df[self._indicators]

            if self._L == 0:
                self._L = len(_df)

            self._stock_df[stock] = _df

        self._data = None
        self.compress_data()

        # pre calcualte the price at every iteration for efficiency
        self._prices = np.array([{stock: self._data[i, s*5]
                                  for s, stock in enumerate(stocks)} for i in range(self._L)])

        # self._stock_indicators = {stock: {indicator: self._data[:, s*5 + i] for i, indicator in enumerate(
        #     self._indicators)} for s, stock in enumerate(stocks)}

        self.sinames = None
        self.sis = {s: dict() for s in stocks}

    def __len__(self):
        return self._L

    def __iter__(self):
        self._i = 0
        self.sinames = [(stock, indicator, i) for i, (stock, indicator) in enumerate(
            product(self.sis, self._indicators))]
        return self

    def __next__(self):
        self._i += 1
        if self._i > len(self):
            raise StopIteration
        for stock, indicator, i in self.sinames:
            self.sis[stock][indicator] = self._data[:self._i, i]
        return self._prices[self._i-1], self.sis

    @property
    def indicators(self):
        return self._indicators

    @property
    def index(self):
        rand_key = [_ for _ in self._stock_df][0]
        return pd.to_datetime(self._stock_df[rand_key].index)

    def compress_data(self):
        self._data = np.concatenate(
            [df.loc[:, df.columns != 'time'].to_numpy() for df in self._stock_df.values()], axis=1).astype('float64')

    def remove_indicator(self, name):
        if name in self._indicators:
            self._indicators.remove(name)
        for stock in self._stocks:
            del self._stock_df[stock][name]

    def add_indicators(self, strategy, to_update):

        for indicator, params in to_update.items():
            if indicator not in self._indicators:
                self._indicators.append(indicator)

            func = strategy.indicator_functions()[indicator]

            for stock in self._stock_df:
                # TODO: add time data back in??
                df = self._stock_df[stock]

                kwargs = dict() if not params else params

                # self._stock_indicators[stock][indicator] = func(df, kwargs)
                self._stock_df[stock][indicator] = func(df, kwargs)

                # print('add indicator', func(df, **kwargs),
                #       self._stock_indicators[stock][indicator])
            self.compress_data()
