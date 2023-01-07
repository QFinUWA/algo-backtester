import numpy as np
import pandas as pd
import os

cdef class StockData:

    def __init__(self, stocks, data_folder):

        self._indicators = ['price', 'volume']
        self._i = 0

        self._stock_df = dict()

        if len(stocks) == 0:
            raise ValueError(
                f'Please provide a list of stocks.')
        
        self._L = 0
        for stock in stocks:

            _df = pd.read_csv(os.path.join(data_folder, f'{stock}.csv'))
            
            if self._L == 0:
                self._L = len(_df)

            self._stock_df[stock] = _df

        self._data = None
        self.compress_data()
        
        # pre calcualte the price at every iteration for efficiency
        cdef int s
        self._prices = np.array([{stock: self._data[i, s*2]
                         for s, stock in enumerate(stocks)} for i in range(self._L)])

    def __len__(self):
        return self._L

    def __iter__(self):
        self._i = 0
        return self

    def __next__(self):
        self._i += 1
        # print('\t', self._i)
        if self._i > len(self):
            raise StopIteration
        return self._prices[self._i-1], self._data[:self._i]

    @property
    def indicators(self):
        return self._indicators

    def compress_data(self):
        self._data = np.concatenate(
            [df.loc[:, df.columns != 'time'].to_numpy() for stock, df in self._stock_df.items()], axis=1).astype('float64')
        

    def remove_indicator(self, name):
        if name in self._indicators:
            self._indicators.remove(name)
        for stock in self._stocks:
            del self._stock_df[stock][name]

    def add_indicators(self, strategy, to_update):

#        if not table:
#            return
#
#        # TODO: check that this works
#        # print(table)
#        if not any(type(name) is str and callable(func) for name, func in table.items()):
#            raise ValueError(
#                f'add_indicator expects a dictionary mapping str to func')
        
        for indicator, params in to_update.items():
            if indicator not in self._indicators:
                self._indicators.append(indicator)

            func = strategy.indicator_functions()[indicator]

            for stock in self._stock_df:
                # TODO: add time data back in??
                df = self._stock_df[stock][['price', 'volume']]
                kwargs = dict() if not params else params
                
                self._stock_df[stock][indicator] = func(df, **kwargs)
            self.compress_data()
