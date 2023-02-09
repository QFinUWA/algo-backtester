import itertools
from tqdm import tqdm
from .opt.portfolio import Portfolio
from .opt.stockdata import StockData
import pandas as pd
from multiprocessing import Pool, managers
from multiprocessing.managers import BaseManager
from functools import partial
import math
from time import time
import collections
from .opt.indicator import Indicators
import numpy as np
import os 

class CustomManager(BaseManager):
    # nothing
    pass

class Backtester:

    def __init__(self, strategy, stocks, data=r'\data', tests=20, cash=1000, fee=0.001):

        self._strategy = strategy
        self._data = StockData(stocks, data)
        self._stocks = stocks
        self._update_indicators = list()

        self._fee = fee
        self._starting_cash = cash
        
        self._analyser = Analyser()
        self._indicator_data = Indicators(stocks)

        self._algorithm_params = dict()
        self._indicator_params = dict()


        self._default_indicator_params = dict()
        self._indicator_cache = dict()

        self._x = data
    @property
    def fee(self):
        return self._fee

    @property
    def stocks(self):
        return self._data.stocks

    '''
    Marks indicators as needing to be updated.
    '''
    def __str__(self):
        return str(self._indicator_cache)


    def update_indicators(self, only=None):

        for indicator in (only or self._data.indicators[2:]):

            if indicator not in self._update_indicators:
                self._update_indicators.append(indicator)

    def set_algorithm_params(self, params):
        self._algorithm_params.update(params)

    def set_indicator_params(self, params):

        # TODO unsecure
        to_update = {k: v for k, v in params.items(
        ) if k not in self._default_indicator_params or self._default_indicator_params.get(k, None) != v}

        if len(to_update) == 0:
            return
        self._default_indicator_params = params

        for indicator, i_params in params.items():
            self._cache_indicator(indicator, i_params)

    def _cache_indicator(self, indicator, i_params):

        if self._indicator_cached(indicator, i_params):
            return

        i_params_tuple = self.params_to_hashable(i_params)

        if indicator not in self._indicator_cache:
            self._indicator_cache[indicator] = dict()

        indicator_functions = self._strategy.indicator_functions()
        self._indicator_cache[indicator][i_params_tuple] = {stock: indicator_functions[indicator](self._data._stock_df[stock], **i_params) for stock in self._stocks}

    def _indicator_cached(self, indicator, params):
        if indicator not in self._indicator_cache:
            return False
        return self.params_to_hashable(params) in self._indicator_cache[indicator]

    def _get_indicator(self, indicator, params):
        return self._indicator_cache[indicator][self.params_to_hashable(params)]

    def params_to_hashable(self, params):
        return tuple(sorted([(p, v) for p, v in params.items()]))

    def run_wrapper(self, args):
        print(args)
        return
        alg_params, ind_params, = data
        return self.run(algorithm_params = alg_params, indicator_params = ind_params, data_iterator=it, progressbar=False)


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

    def run(self, algorithm_params = None, indicator_params = None, progressbar=True):

        if bool(algorithm_params):
            if not isinstance(algorithm_params, dict):
                raise TypeError(f'algorithm_params must be of type dict, not {type(algorithm_params)}')
        else:
            if not self._algorithm_params:
                raise ValueError('No default algorithm parameters specified')
            algorithm_params = self._algorithm_params


        if bool(indicator_params):
            if not isinstance(algorithm_params, dict):
                raise TypeError(f'indicator_params must be of type dict, not {type(indicator_params)}')
        else:
            if not self._default_indicator_params:
                raise ValueError('No default indicator parameters specified')
            indicator_params = self._default_indicator_params


        # TODO check instaniated
        # backtesting an instance of a strategy

        portfolio = Portfolio(self._stocks, self._starting_cash,
                              self._fee, len(self._data))

        algorithm = self._strategy(*tuple(), **algorithm_params or None)
        indicators = Indicators(self._stocks)
        is_cached = {indicator for indicator, params in indicator_params.items() if self._indicator_cached(indicator, params)}
        indicators.add_indicators({indicator: self._get_indicator(indicator, params) for indicator, params in indicator_params.items() if indicator in is_cached})

        # caclulate indicators 
        # TODO: only calculate indicators that are needed
        # indicators.add_indicators(self._strategy, self._data, self._indicator_params)

        zipped = zip([self._data.get(i) for i in range(len(self._data))], indicators)
        it = tqdm(iter(zipped), total=len(self._data)) if progressbar else iter(zipped)
        for params in it:
            algorithm.run_on_data(params, portfolio)
        # print(portfolio)

        # TODO - manually close positions

        # ret = Result()

        # ret.time_index = pd.DatetimeIndex(self._data.index)
        # ret.hist = portfolio.history
        # ret.fee = self._fee
        # ret.indicator_params = self._indicator_params.copy()
        # ret.algorithm_params = self._algorithm_params.copy()
        # ret.initial_balance = self._starting_cash
        # self._analyser.parse_result(ret)
        # return ret
        cash, longs, shorts = portfolio.history

        res = Result(cash, longs, shorts, self._data.index, (algorithm_params, indicator_params), self._stocks, self._fee)
        print(res)
        # print(portfolio.history)


def run_wrapper(args):
    portfolio, algorithm, indicators, algorithm_params, indicator_params, data_iterator = args
    return run(portfolio, algorithm, indicators, algorithm_params, indicator_params, data_iterator, progressbar=False)

def get_indicator(cache, indicator, params):
    return cache.get(indicator).get(params_to_hashable(params))

def params_to_hashable(params):
    return tuple(sorted([(p, v) for p, v in params.items()]))

def run(portfolio, algorithm, indicator_cache, algorithm_params, indicator_params, stockdata, progressbar=True):

    # TODO check instaniated
    # backtesting an instance of a strategy

    algorithm = algorithm(*tuple(), **algorithm_params or None)
    indicators = Indicators(portfolio._stocks)
    indicators.add_indicators({indicator: get_indicator(indicator_cache, indicator, params) for indicator, params in indicator_params.items()})

    # caclulate indicators 
    # TODO: only calculate indicators that are needed
    # indicators.add_indicators(self._strategy, self._data, self._indicator_params)

    zipped = zip([stockdata.get(i) for i in range(stockdata.len())], indicators)
    it = tqdm(iter(zipped)) if progressbar else iter(zipped)
    for params in it:
        algorithm.run_on_data(params, portfolio)
    
    # print(portfolio)

    # ret = Result()
    # df_ret = portfolio.history
    # df_ret['time'] = pd.DatetimeIndex(self._data.index)
    # ret.hist = df_ret

    # ret.fee = self._fee
    # ret.indicator_params = self._indicator_params.copy()
    # ret.algorithm_params = self._algorithm_params.copy()
    # ret.initial_balance = self._starting_cash

    
    return portfolio.cash


class Analyser:

    def __init__(self):
        self._i = 0
        return

    def parse_result(self, result):


        # store in hdf5 file format
        with pd.HDFStore(f'del/{self._i:02}.hdf5') as store:
            print(f"Saving to {f'del/{self._i:02}.hdf5'}")
            cash_hist, df = result.hist
            df = pd.DataFrame(df)
            store.put('results', df)
            store.put('time_index', pd.Series(result.time_index))
            store.put('cash_history', pd.Series(cash_hist))
            store.get_storer('results').attrs.metadata = {"fee": result.fee, 
                                                        "indicator_params": result.indicator_params, 
                                                        "algorithm_params": result.algorithm_params,
                                                        }
            self._i += 1

class Result:

    def __init__(self, cash, longs, shorts, time, params, stocks, fee):
        self.algorithm_params, self.indicator_params = params
        self.fee = fee
        self.initial_balance = cash[0]

        self.time_index = time

        self.stats = self.parse(stocks, longs, shorts)

    
    def parse(self, stocks, longs, shorts):

        # time, stock, profit
        df = pd.DataFrame()

        for stock in stocks:
            l = [p for _,s,p in longs if s == stock] or [0]
            s = [p for _,s,p in shorts if s == stock] or [0]

            m_l = np.mean(l)
            m_s = np.mean(s)


            df[stock] = [
                        len(l) + len(s),   (m_l + m_s)/2,   np.std(l + s), 
                        len(l),             m_l,            np.std(l),  
                        len(s),             m_s,            np.std(s)
                        ]
        
        a_longs, a_shorts = [p for *_,p in longs] or [0], [p for *_,p in shorts] or [0]

        m_l = np.mean(a_longs)
        m_s = np.mean(a_shorts)
        
        df['Total'] = [
                    len(a_longs) + len(a_shorts),  (m_l + m_s)/2,   np.std(a_longs + a_shorts), 
                    len(a_longs),                   m_l,            np.std(a_longs),  
                    len(a_shorts),                  m_s,            np.std(a_shorts)
                    ]

        df.fillna(0, inplace=True)

        df.index = [f'{b}_{a}' for a,b in itertools.product(['trades', 'longs', 'shorts'], ["n", 'mean_per', 'std'])]
        

        return df
                

    def __str__(self):
        return f'{self.algorithm_params}\n{self.indicator_params}\nStarting Balance:\t{self.initial_balance}\nFee:\t\t\t{self.fee}\n{self.stats}'





