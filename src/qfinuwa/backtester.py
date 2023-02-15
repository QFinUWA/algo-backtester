
import itertools
from .opt.portfolio import Portfolio
from .opt.stockdata import StockData
import pandas as pd
from time import time
import collections
from .opt.indicators import Indicators
import numpy as np
import random
from tabulate import tabulate
from .opt.result import Result, ResultsContainer, SweepResults
import math

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

    def __init__(self, stocks, data=r'\data', strategy=None, days='all', cash=1000, fee=0.001, seed=None):

        self._data = StockData(stocks, data, verbose=True)

        self._precomp_prices = self._data.prices

        self._stocks = stocks

        self._fee = fee
        self._starting_cash = cash
        
        self._algorithm_params = dict()

        self._indicator_cache = Indicators(stocks, self._data._stock_df)

        self._days = days

        self._strategy = None
        if strategy is not None:
            self.update_algorithm(strategy)

        self.seed = seed

        self.random = random

    def update_days(self, days):
        self._days = days

    def update_seed(self, seed):
        self.seed = seed

    @property
    def indicator_params(self):
        return self._indicator_cache.defaults
            
    @property
    def fee(self):
        return self._fee

    @property
    def stocks(self):
        return self._data.stocks

    def update_algorithm(self, algorithm):
        self._strategy = algorithm
        self._indicator_cache.update_algorithm(algorithm)


    def __str__(self):
        return str(self._indicator_cache)

    
    @property
    def algorithm_params(self):
        x = self._strategy.defaults()['algorithm']
        x.update(self._algorithm_params)  
        return x

    def set_algorithm_params(self, params):

        if not self._strategy:
            raise ValueError('No algorithm specified')
        
        self._algorithm_params.update({k:v for k,v in params.items() if k in self._strategy.defaults()['algorithm']})

    @property
    def indicator_params(self):
        return self._indicator_cache.defaults
        
    def set_indicator_params(self, params):
        
        self._indicator_cache.set_default(params, self._strategy)


    def backtest_strategies(self, strategy_params, indicator_params, cv = 1, seed=None):
        # get all combinations of algorithm paramters
        
        if strategy_params.keys() - self._strategy.defaults()['algorithm'].keys():
            raise ValueError('Invalid algorithm parameters')
        
        strategy_params = {**self.algorithm_params, **strategy_params}

        if indicator_params.keys() - self._indicator_cache.defaults.keys():
            raise ValueError('Invalid indicator name')

        # indicator_params = {**self.indicator_params, **indicator_params}
        for indicator, paramters in indicator_params.items():
            if paramters.keys() - self._indicator_cache.defaults[indicator].keys():
                raise ValueError('Invalid indicator parameters')
            indicator_params[indicator] = {**self._indicator_cache.defaults[indicator], **paramters}

        print('> Backtesting the across the following ranges:')
        print('Agorithm Parameters', strategy_params)
        print('Indicator Parameters', indicator_params)

        param, val = zip(*strategy_params.items())

        val = map(lambda v: v if isinstance(v, list) else [v], val)

        strategy_comb = [dict(zip(param, v)) for v in itertools.product(*val)]

        # # precompute all indicators and store in dictionary
        len_indicator_comb = math.prod(len(values if isinstance(values, list) else [values]) for paramters in indicator_params.values() for values in paramters.values())     
        indicator_comb = collections.defaultdict(list)

        with tqdm(total=len_indicator_comb, desc="Precomputing indicator variants.") as bar:
            for indicator, paramters in indicator_params.items():
                
                param, val = zip(*paramters.items())

                val = map(lambda v: v if isinstance(v, list) else [v], val)

                permutations_dicts = [dict(zip(param, v))
                                for v in itertools.product(*val)]

                for perm in permutations_dicts:

                    self._indicator_cache.add(indicator, perm, self._strategy)
                    indicator_comb[indicator].append(perm)
                    bar.update(1)

        # get every combination of different indicators
        trials = [dict(zip(indicator_comb.keys(), c)) for c in itertools.product(*indicator_comb.values())]
        s = time()

        # 
        # run
        seed = seed or self.random.randint(0, 2**32)
        res = []
        print('Running backtests...')
        for alg_params, ind_params in tqdm(itertools.product(strategy_comb, trials), total=len(strategy_comb) * len(trials), desc=f"Running paramter sweep (cv={cv})"):
            res.append(self.run(algorithm_params=alg_params, indicator_params=ind_params, cv=cv, seed=seed, progressbar=False))
        
        return SweepResults(res)
        
        if not multiprocessing:
            res = []
            print('Running backtests...')
            for alg_params, ind_params in itertools.product(strategy_comb, trials):
                print(alg_params, ind_params)
                res.append(self.run(algorithm_params=alg_params, indicator_params=ind_params, progressbar=False))
        else:
            CustomManager.register('StockData', StockData)
            CustomManager.register('dict', dict)
            with CustomManager() as manager:
                stockdata = manager.StockData(self._stocks, self._x)
                portfolios = [Portfolio(self._stocks, self._starting_cash, self._fee, self._data.len()) for _ in range(len(strategy_comb) * len(trials))]
                alg = self._strategy
                indicator_cache = manager.dict(self._indicator_cache)
                print('Running backtests...')
                with Pool(processes=4) as p:
                    res = p.map(run_wrapper, [(portfolios, alg, indicator_cache, strat, ind, stockdata) for (strat, ind), portfolios in zip(itertools.product(strategy_comb, trials), portfolios)])
# portfolio, algorithm, indicators, algorithm_params, indicator_params, data_iterator
        print(time() - s)
        print(res)
        return res

    '''
    Backtests the stored strategy. 
    '''

    def run(self, algorithm_params = None, indicator_params = None, progressbar=True, cv=1, seed=None):

        if bool(algorithm_params):
            if not isinstance(algorithm_params, dict):
                raise TypeError(f'algorithm_params must be of type dict, not {type(algorithm_params)}')
        else:
            if not self._algorithm_params and self._strategy.defaults()['algorithm']:
                raise ValueError('No default algorithm parameters specified')
            algorithm_params = self.algorithm_params

        if bool(indicator_params):
            if not isinstance(algorithm_params, dict):
                raise TypeError(f'indicator_params must be of type dict, not {type(indicator_params)}')
            print(indicator_params)
            self._indicator_cache.set_default(indicator_params, self._strategy)
        else:
            if not self._indicator_cache.defaults:
                raise ValueError('No default indicator parameters specified')
            indicator_params = self._indicator_cache.defaults


        # caclulate indicators 
        data = list(zip(*self._precomp_prices, self._indicator_cache))

        self.random.seed(seed or random.randint(0, 2**32))
        random_periods = self.get_random_periods(cv) 

        results = []

        desc = f'> Running backtest over {cv} sample{"s" if cv > 1 else ""} of {self._days} day{"s" if cv > 1 else ""}'
        for start, end in (tqdm(random_periods, desc = desc) if progressbar and cv > 1 else random_periods):
            portfolio = Portfolio(self._stocks, self._starting_cash, self._fee)
            if algorithm_params:
                algorithm = self._strategy(*tuple(), **algorithm_params)
            else:
                algorithm = self._strategy(*tuple())
            
            test = data[start:end]
            #---------[RUN THE ALGORITHM]---------#
            for params in (tqdm(test, desc=desc) if progressbar and cv == 1 else test):
                algorithm.run_on_data(params, portfolio)
            cash, longs, shorts = portfolio.wrap_up()
            results.append(Result(self._stocks, self._data, self._data.index, (start, end), cash, longs, shorts ))
            #-------------------------------------#

        return ResultsContainer((algorithm_params, indicator_params), results)

    def get_random_periods(self, n):

        if self._days == 'all':
            return [(0, len(self._data)) for _ in range(n)]

        days = self._data.index.dt.to_period('D').drop_duplicates()

        s_is = self.random.sample(range(len(days) - self._days), n)

        starts = (str(days.iloc[s_i]) for s_i in s_is)
        ends = (str(days.iloc[s_i+self._days]) for s_i in s_is)

        return [(self._data._index[self._data._index >= start].index[0], self._data._index[self._data._index < end].index[-1]) for start, end in zip(starts, ends)]




