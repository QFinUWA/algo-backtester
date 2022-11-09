import pandas as pd
import numpy as np
import itertools
from tqdm import tqdm
from opt.portfolio cimport Portfolio
from opt.stockdata cimport StockData
from opt.API import API
from cyalgorithm cimport CythonAlgorithm



cdef class CythonBacktester:

    def __init__(self, stocks=['apple'], period='2022-2023', frequency='1T', sample_period='3 months', overlap=True, samples=20):

        self._data = StockData(
            stocks=stocks, period=period, frequency=frequency)
        self._stocks = stocks
        self._update_indicators = list()

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

    def _calculate_indicators(self, strategy):
        self._data.add_indicators(strategy.indicator_functions, strategy.indicator_parameters)
        self._update_indicators = list()

    '''
    Backtests a strategy with a starting balance and fee. 

    Accepts either an instance of an algorithm.
    '''

    def backtest_strategy(self, strategy, cash=1000, fee=0.005):
        # backtesting an instance of a strategy

        if not issubclass(type(strategy), CythonAlgorithm):
            raise ValueError(
                f'backtest_strategy() arg 1 must be an Algorithm not {type(strategy)}')

        self._calculate_indicators(strategy)

        portfolio = Portfolio(self._stocks, cash, fee, len(self._data))

        cdef dict curr_prices
        cdef np.float64_t[:, :] all_prices
        for curr_prices, all_prices in tqdm(iter(self._data)):
            strategy.run_on_data(curr_prices, all_prices, portfolio)

        return portfolio.history

    '''
    TODO: Add paramter to only recalculate certrain indicators
    '''

    def backtest_straties(self, strategy, parameters, cash=1000, fee=0.005, recalculate_indicators=True):
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
                strategy_instance, cash=cash, fee=fee))
        # return results
        return 1