
import itertools
from .opt.portfolio import Portfolio
from .opt.stockdata import StockData
import pandas as pd
from time import time
import collections
import numpy as np
import random
from tabulate import tabulate
from .opt.result import SingleRunResult, MultiRunResult, ParameterSweepResult
import math
from .algorithm import Algorithm
from .indicators import Indicators

from itertools import islice

from IPython import get_ipython

try:
    shell = get_ipython().__class__.__name__
    if shell in ['ZMQInteractiveShell']:
        from tqdm import tqdm_notebook as tqdm   # Jupyter notebook or qtconsole or Terminal running IPython  
    else:
         from tqdm import tqdm   
except NameError:
    from tqdm import tqdm      # Probably standard Python interpreter

    

class Backtester:

    def __init__(self, stocks, strategy, pindicators, data=r'\data', days='all', cash=1000, fee=0.001, seed=None):

        # raise execption if strategy is not a subclass of Strategy
        if not issubclass(strategy, Algorithm):
            raise ValueError('Strategy must be a subclass of Algorithm')   
        self._strategy = strategy

        self._data = StockData(data, stocks=stocks, verbose=True)
        self._precomp_prices = self._data.prices

        # raise expection if indiators is not a subclass of Indicators
        if not issubclass(pindicators, Indicators):
            raise ValueError('Indicators must be a subclass of Indicators')
        
        self._indicators = pindicators(self._data)

        self._fee = fee
        self._starting_cash = cash
        
        self._algorithm_params = dict()

        self._days = days

        self._random = random

    def update_days(self, days):
        self._days = days


    def add_indicator(self, name, func):
        pass
        
    @property
    def indicator_params(self):
        return self._indicators.params
            
    @property
    def fee(self):
        return self._fee

    @property
    def stocks(self):
        return self._data.stocks

    @property
    def algorithm_params(self):
        x = self._strategy.defaults()
        x.update(self._algorithm_params)  
        return x

    def set_algorithm_params(self, params):

        if not self._strategy:
            raise ValueError('No algorithm specified')
        self._algorithm_params.update({k:v for k,v in params.items() if k in self._strategy.defaults()})

    def update_algorithm(self, algorithm):
        self._strategy = algorithm

        if algorithm.defaults().keys() - self.algorithm_params.keys():
            print('! Algorithm parameters changed: resetting to defaults !')
            self.algorithm_params = algorithm.defaults()


    def update_indicators(self, pindicators):
        self._indicators = pindicators(self._data)

    def __str__(self):
        return  f'Backtester:\n' + \
                f'- Strategy: {self._strategy.__name__}\n' + \
                f'\t- Params: {self.algorithm_params}\n' + \
                f'- Indicators: {self._indicators.__class__.__name__}\n' + \
                f'\t- Params: {self.indicator_params}\n' + \
                f'\t- Indicator Groups: {self._indicators.indicator_groups}\n' + \
                f'\t- SingleIndicators: {self._indicators._singles}\n' \
                f'\t- MultiIndicators: {self._indicators._multis}\n' \
                f'- Stocks: {self.stocks}\n' + \
                f'- Fee {self.fee}\n' + \
                f'- Days: {self._days}\n'
    
    def __repr__(self):
        return self.__str__()

    def set_indicator_params(self, params):
        self._indicators.update_parameters(params)


    def run_grid_search(self, strategy_params = None, indicator_params = None, cv = 1, seed=None):
        # get all combinations of algorithm paramters
        # ----[strategy params]----
        strategy_params = strategy_params or dict()

        if strategy_params.keys() - self.algorithm_params.keys():
            raise ValueError('Invalid algorithm parameters')

        default_strategy_params = {**self.algorithm_params, **strategy_params}
        param, val = zip(*default_strategy_params.items())
        val = map(lambda v: v if isinstance(v, list) else [v], val)
        strategy_params_list = [dict(zip(param, v)) for v in itertools.product(*val)]

        # ----[indicator params]----
        
        indicator_params = indicator_params or dict()
        indicator_params_list = self._indicators.get_permutations(indicator_params)


        print('> Backtesting the across the following ranges:')
        print('Agorithm Parameters', default_strategy_params)
        print('Indicator Parameters', self._indicators._fill_in_defaults(indicator_params))

        # run
        seed = seed or self._random.randint(0, 2**32)
        res = []
        print('Running backtests...')
        for alg_params, ind_params in tqdm(itertools.product(strategy_params_list, indicator_params_list), total=len(strategy_params_list) * len(indicator_params_list), desc=f"Running paramter sweep (cv={cv})"):
            res.append(self.run(algorithm_params=alg_params, indicator_params=ind_params, cv=cv, seed=seed, progressbar=False))
        
        return ParameterSweepResult(res)
        # TODO: add something to deal with reading nan values in portfolio

    '''
    Backtests the stored strategy. 
    '''

    def run(self, algorithm_params = None, indicator_params = None, progressbar=True, cv=1, seed=None):

        if not self._strategy:
            raise ValueError('No algorithm specified')

        if bool(algorithm_params):
            if not isinstance(algorithm_params, dict):
                raise TypeError(f'algorithm_params must be of type dict, not {type(algorithm_params)}')

            # fill in missing parameters with defaults
            alg_defaults = self._strategy.defaults()
            alg_defaults.update(algorithm_params)
            algorithm_params = alg_defaults
        else:
            algorithm_params = self.algorithm_params

        if bool(indicator_params):
            if not isinstance(indicator_params, dict):
                raise TypeError(f'indicator_params must be of type dict, not {type(indicator_params)}')
            self._indicators.add_parameters(indicator_params)
        else:
            indicator_params = self._indicators.params

        self._random.seed(seed or random.randint(0, 2**32))
        random_periods = self.get_random_periods(cv) 
        results = []

        # caclulate indicators 
        data = zip(*self._precomp_prices, self._indicators.iterate_params(indicator_params))

        # precomp_indicators = 4.e-7 * np.mean([r[1] - r[0] for r in random_periods]) * cv

        # if precomp_indicators:
        #     data = list(data)

        # print(list((zip(*self._precomp_prices)))[0])


        desc = f'> Running backtest over {cv} sample{"s" if cv > 1 else ""} of {self._days} day{"s" if cv > 1 else ""}'
        for start, end in (tqdm(random_periods, desc = desc) if progressbar and cv > 1 else random_periods):
            portfolio = Portfolio(self.stocks, self._starting_cash, self._fee)
            if algorithm_params:
                algorithm = self._strategy(*tuple(), **algorithm_params)
            else:
                algorithm = self._strategy(*tuple())
            # if precomp_indicators:
                # test = data[start:end]
            # else:
            test = islice(data, start, end) 
            
            # TODO: test speed
            # TODO: test speed of .get
            #---------[RUN THE ALGORITHM]---------#
            for params in (tqdm(test, desc=desc, total = end-start, mininterval=0.5) if progressbar and cv == 1 else test):
                
                algorithm.run_on_data(params, portfolio)
            cash, longs, shorts = portfolio.wrap_up()
            results.append(SingleRunResult(self.stocks, self._data, self._data.index, (start, end), cash, longs, shorts ))
            #-------------------------------------#

        return MultiRunResult((algorithm_params, indicator_params), results)

    def get_random_periods(self, n):

        if self._days == 'all':
            return [(0, len(self._data)) for _ in range(n)]

        days = self._data.index.dt.to_period('D').drop_duplicates()
    
        s_is = self._random.sample(range(len(days) - self._days), n)

        starts = (str(days.iloc[s_i]) for s_i in s_is)
        ends = (str(days.iloc[s_i+self._days]) for s_i in s_is)

        return [(self._data._index[self._data._index >= start].index[0], self._data._index[self._data._index < end].index[-1]) for start, end in zip(starts, ends)]




