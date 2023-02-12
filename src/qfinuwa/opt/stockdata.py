import numpy as np
import pandas as pd
import os
from itertools import product


class StockData:

    def __init__(self, stocks, data):

        self._indicators = ['open', 'close', 'high', 'low', 'volume']
        self._i = 0

        self._stock_df = dict()

        if len(stocks) == 0:
            raise ValueError(
                f'Please provide a list of stocks.')

        self._L = 0
        self._index = None


        for stock in stocks:

            _df = pd.read_csv(os.path.join(data, f'{stock}.csv'))
            
            if self._L == 0:
                self._L = len(_df)
                self._index = _df['time']

            self._stock_df[stock] = _df[self._indicators]
        self._data = self.compress_data()


        # pre calcualte the price at every iteration for efficiency
        self._prices = np.array([{stock: self._data[i, 1 + s*5]
                                for s, stock in enumerate(stocks)} for i in range(self._L)])

        self.sis = {s: dict() for s in stocks}
        self.sinames = [(stock, indicator, i) for i, (stock, indicator) in enumerate(
                        product(self.sis, self._indicators))]

    @property
    def prices(self):
        siss = []
        for index in range(len(self)):
            A = {stock: dict() for stock in self.sis}
            for stock, indicator, i in self.sinames:
                A[stock][indicator] = self._data[:index, i]
            siss.append(A)
        return self._prices, siss

    def get(self, index):

        for stock, indicator, i in self.sinames:
            self.sis[stock][indicator] = self._data[:index, i]
        
        return self.sis

    def len(self):
        return self._L
    
    def __len__(self):
        return self._L

    @property
    def index(self):
        return self._index

    def compress_data(self):

        return np.concatenate(
            [df.loc[:, df.columns != 'time'].to_numpy() for df in self._stock_df.values()], axis=1).astype('float64')
