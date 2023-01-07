import pandas as pd
import numpy as np
import itertools
from tqdm import tqdm
from opt.portfolio cimport Portfolio
from opt.stockdata import StockData
from cyalgorithm cimport CythonAlgorithm


cdef class CythonBacktester:

    def __init__(self, strategy, stocks, data=r'\data', tests=20, cash=10000, fee=0.005):

        self._strategy = strategy
        self._data = StockData(stocks, data)
        self._stocks = stocks
        self._update_indicators = list()
        self._cash = cash
        self._fee = fee
        self._algorithm_params = dict()
        self._indicator_params = dict()

    @property
    def fee(self):
        return self._fee

    @property
    def stocks(self):
        return self._data.stocks

    '''
    Marks indicators as needing to be updated.
    '''
    def update_indicators(self, only = None):

        for indicator in (only or self._data.indicators[2:]):

            if indicator not in self._update_indicators:
                self._update_indicators.append(indicator)

#    def _calculate_indicators(self, strategy):
#        self._data.add_indicators(strategy.indicator_functions, strategy.indicator_parameters)
#        self._update_indicators = list()

    def set_algorithm_params(self, params):
        self._algorithm_params.update(params)

    def set_indicator_params(self, params):

        # TODO unsecure
        to_update = {k:v for k,v in params.items() if k not in self._indicator_params or self._indicator_params.get(k, None) != v}


        if len(to_update) == 0:
            return

        self._data.add_indicators(self._strategy, to_update)
        self._indicator_params.update(params)


    '''
    TODO: Add paramter to only recalculate certrain indicators
    '''

    def backtest_straties(self, strategy, parameters, recalculate_indicators=True):
        # backtesting a range of instances (maybe this should be a separate function?)

        keys, values = zip(*parameters.items())
        permutations_dicts = [dict(zip(keys, v))
                              for v in itertools.product(*values)]
        results = list()
        for paramter_instance in permutations_dicts:
            strategy_instance = strategy(**paramter_instance)
            if recalculate_indicators:
                self._calculate_indicators(strategy_instance)

            results.append(self.backtest_strategy(
                strategy_instance, cash=self._cash, fee=self._fee))
        # return results
        return 1

    '''
    Backtests the stored strategy. 
    '''

    def backtest_strategy(self):
        
        algorithm = self._strategy(*tuple(), **self._algorithm_params or None)

        # TODO check instaniated
        
        # backtesting an instance of a strategy

        portfolio = Portfolio(self._stocks, self._cash, self._fee, len(self._data))

        cdef dict curr_prices
        cdef dict all_prices
        for curr_prices, all_prices in tqdm(iter(self._data)):
            algorithm.run_on_data(curr_prices, all_prices, portfolio)

        return portfolio.history