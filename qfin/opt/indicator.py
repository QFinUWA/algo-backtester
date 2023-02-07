import numpy as np
import pandas as pd
import os
from itertools import product


class Indicators:

    def __init__(self, stocks):

        self._i = 0

        self._params = dict()

        self._stocks = stocks

        self._indicators = {}
        self._curr_indicators = None
        self._stock_indicators = None
        self._L = 0

    # def add_indicators(self, strategy, data, to_update):

    #     for indicator, params in to_update.items():
    #         if indicator not in self._indicators:
    #             for stock in self._stocks:
    #                 self._indicators[indicator] = {stock: None for stock in self._stocks}
                
    #         func = strategy.indicator_functions()[indicator]

    #         values = []
    #         for stock in self._stocks:
            
    #             df = data._stock_df[stock]

    #             self._L = len(df) if self._L == 0 else self._L

    #             kwargs = dict() if not params else params

    #             # self._stock_indicators[stock][indicator] = func(df, kwargs)
    #             values.append(func(df, **kwargs).to_numpy())

    #         self._indicators[indicator] = np_values

    def add_indicators(self, indicators):
        # TODO: security
        for indicator, stock_values in indicators.items():
            # if indicator not in self._indicators:
            #     raise ValueError(f'Indicator {indicator} not in {self._indicators}')

            if indicator not in self._indicators:
                self._indicators[indicator] = {stock: None for stock in self._stocks}

            for values in stock_values.values():
                self._L = len(values) if self._L == 0 else self._L
            self._indicators[indicator] = np.stack([values for values in stock_values.values()], axis=1)


    def remove_indicator(self, name):
        
        if name in self._indicators:         
            del self._indicators[name]
        
    def remove_indicators(self):
        self._indicators = {}
        self._L = 0
    

    def calc_indicator(self, strategy, indicator, kwargs):
        # TODO: security
        func = strategy.indicator_functions()[indicator]
        return {stock: func(self._stock_df[stock], **kwargs).to_numpy() for stock in self._stock_df}
        
    def __len__(self):
        return self._L

    def __iter__(self):
        self._i = 0
        self._curr_indicators = {stock: {indicator: None for indicator in self._indicators} for stock in self._stocks}
        self._indexes = product(range(len(self._stocks)), self._indicators)
        return self

    def __next__(self):
        self._i += 1
        if self._i > len(self):
            raise StopIteration
        for s, indicator in self._indexes:  
            self._curr_indicators[self._stocks[s]][indicator] = self._indicators[indicator][:self._i, s]
        
        return self._curr_indicators
