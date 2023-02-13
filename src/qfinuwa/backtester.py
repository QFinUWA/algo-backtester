
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
from .opt.result import Result, ResultsContainer

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
        self._indicator_params = dict()

        self._indicator_cache = Indicators(stocks, self._data._stock_df)

        self._days = days

        self._strategy = None
        if strategy is not None:
            self.update_algorithm(strategy)

        self.seed = seed

    def update_days(self, days):
        self._days = days

    def update_seed(self, seed):
        self.seed = seed
            
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


    def backtest_strategies(self, strategy_params, indicator_params, multiprocessing=True):
        # get all combinations of algorithm paramters
        param, val = zip(*strategy_params.items())
        strategy_comb = [dict(zip(param, v)) for v in itertools.product(*val)]

        # # precompute all indicators and store in dictionary
        len_indicator_comb = sum(len(values) for paramters in indicator_params.values() for values in paramters.values())     

        indicator_comb = collections.defaultdict(list)

        with tqdm(total=len_indicator_comb, desc="Precomputing indicator variants.") as bar:
            for indicator, paramters in indicator_params.items():
                
                param, val = zip(*paramters.items())

                permutations_dicts = [dict(zip(param, v))
                                for v in itertools.product(*val)]

                for perm in permutations_dicts:

                    self._cache_indicator(indicator, perm)
                    indicator_comb[indicator].append(perm)
                    bar.update(1)

        # get every combination of different indicators
        trials = [dict(zip(indicator_comb.keys(), c)) for c in itertools.product(*indicator_comb.values())]
        s = time()

        # 
        # run
        res = []
        print('Running backtests...')
        for alg_params, ind_params in itertools.product(strategy_comb, trials):
            print(alg_params, ind_params)
            res.append(self.run(algorithm_params=alg_params, indicator_params=ind_params, progressbar=False))
        
        return res
        
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

    def run(self, algorithm_params = None, indicator_params = None, progressbar=True, cv=1):

        if bool(algorithm_params):
            if not isinstance(algorithm_params, dict):
                raise TypeError(f'algorithm_params must be of type dict, not {type(algorithm_params)}')
        else:
            if not self._algorithm_params:
                raise ValueError('No default algorithm parameters specified')
            algorithm_params = self.algorithm_params


        if bool(indicator_params):
            if not isinstance(algorithm_params, dict):
                raise TypeError(f'indicator_params must be of type dict, not {type(indicator_params)}')
        else:
            if not self._indicator_cache.defaults:
                raise ValueError('No default indicator parameters specified')
            indicator_params = self._indicator_cache.defaults

        # caclulate indicators 
        data = list(zip(*self._precomp_prices, self._indicator_cache))

        random_periods = [0, len(self._data)]*cv if self._days == 'all' else self.get_random_periods(cv) 

        results = []

        desc = f'> Running backtest over {cv} sample{"s" if cv > 1 else ""} of {self._days} day{"s" if cv > 1 else ""}'
        for start, end in (tqdm(random_periods, desc = desc) if progressbar and cv > 1 else random_periods):
            portfolio = Portfolio(self._stocks, self._starting_cash, self._fee)
            algorithm = self._strategy(*tuple(), **algorithm_params or None)
            
            test = data[start:end]
            #---------[RUN THE ALGORITHM]---------#
            for params in (tqdm(test, desc=desc) if progressbar and cv == 1 else test):
                algorithm.run_on_data(params, portfolio)
            cash, longs, shorts = portfolio.wrap_up()
            results.append(Result(self._stocks, cash, longs, shorts, self._data.index[start:end]))
            #-------------------------------------#

        results = ResultsContainer((algorithm_params, indicator_params), results)

        return results

    def get_random_periods(self, n):
        rand = random if not self.seed else random.RandomState(self.seed) 

        days = self._data.index.dt.to_period('D').drop_duplicates()

        s_is = rand.sample(range(len(days) - self._days), n)

        starts = (str(days.iloc[s_i]) for s_i in s_is)
        ends = (str(days.iloc[s_i+self._days]) for s_i in s_is)

        return [(self._data._index[self._data._index >= start].index[0], self._data._index[self._data._index < end].index[-1]) for start, end in zip(starts, ends)]




