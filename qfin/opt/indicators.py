import numpy as np
import pandas as pd
import os
from itertools import product


class Indicators:

    def __init__(self, stocks):

        self._params = dict()
        self._stocks = stocks
        self._curr_indicators = None
        self._cache = dict()

    #
    def add(self, indicator, i_params, strategy, data):

        if self._is_cached(indicator, i_params):
            return

        i_params_tuple = self.params_to_hashable(i_params)

        if indicator not in self._cache:
            self._cache[indicator] = dict()

        indicator_functions = strategy.indicator_functions()
        self._cache[indicator][i_params_tuple] = {stock: indicator_functions[indicator](data[stock], **i_params) for stock in data}

    #
    def _is_cached(self, indicator, params):
        if indicator not in self._cache:
            return False
        return self.params_to_hashable(params) in self._cache[indicator]

    #
    def _get_indicator(self, indicator, params):

        if not self._is_cached(indicator, params):
            return None

        return self._cache[indicator][self.params_to_hashable(params)]

    #
    def params_to_hashable(self, params):
        return tuple(sorted([(p, v) for p, v in params.items()]))
        

    # we aren't using iterators here because this object needs to be a shared object
    def iterate(self, params):
        self._indicators = dict()
        for indicator, i_params in params.items():
            stock_values = self._get_indicator(indicator, i_params)
            if stock_values is None:
                raise ValueError(f'Indicator {indicator} with params {i_params} not found.')
            self._indicators[indicator] = np.stack([values for values in stock_values.values()], axis=1)
        
        self._curr_indicators = {stock: {indicator: None for indicator in params} for stock in self._stocks}  
        self._indexes = product(range(len(self._stocks)), self._indicators)
        self._L = len(self._indicators[list(self._indicators.keys())[0]])

    def get(self, i):

        if i >= self._L:
            raise ValueError(f'Index {i} out of range.')

        for s, indicator in self._indexes:  
            self._curr_indicators[self._stocks[s]][indicator] = self._indicators[indicator][:i, s]
        
        return self._curr_indicators
