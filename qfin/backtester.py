
import itertools
from tqdm import tqdm
from .opt.portfolio import Portfolio
from .opt.stockdata import StockData
import pandas as pd
from multiprocessing import Pool, Manager
from multiprocessing.managers import BaseManager
from functools import partial
import math
from time import time
import collections
from .opt.indicators import Indicators
import numpy as np


def run_wrapper(i, portfolio, algorithm, it):
    for params in tqdm(it):
        algorithm.run_on_data(params, portfolio)
    portfolio.wrap_up()
    return portfolio.history


class Backtester:

    def __init__(self, stocks, data=r'\data', strategy=None, months=3, cash=1000, fee=0.001):

        print('Fetching data...')
        self._data = StockData(stocks, data)
        print('pre')
        self._precomp_prices = self._data.prices

        self._stocks = stocks

        self._fee = fee
        self._starting_cash = cash
        
        self._analyser = Analyser()

        self._algorithm_params = dict()
        self._indicator_params = dict()


        print('Creating Indicators')
        self._indicator_cache = Indicators(stocks, self._data._stock_df)

        self._months = months

        self._x = data

        self._strategy = None
        if strategy is not None:
            self.update_algorithm(strategy)
            
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
            print('def', indicator_params)

        # TODO check instaniated
        # backtesting an instance of a strategy

        # algorithm = self._strategy(*tuple(), **algorithm_params or None)
        # indicators = Indicators(self._stocks)
        # is_cached = {indicator for indicator, params in indicator_params.items() if self._indicator_cached(indicator, params)}
        # indicators.add_indicators({indicator: self._get_indicator(indicator, params) for indicator, params in indicator_params.items() if indicator in is_cached})

        # caclulate indicators 
        # TODO: only calculate indicators that are needed
        # indicators.add_indicators(self._strategy, self._data, self._indicator_params)
        print('Preparing Tests')
        self._indicator_cache.iterate(indicator_params)

        # TODO: cache this
        self._data.index 

        # print the size of zipped in bytes

        # print('Populating process data')
        # algs = [self._strategy(*tuple(), **algorithm_params or None) for _ in range(N)]
        # ports = [ for _ in range(N)]

        # print('Starting Tests')
        # with Pool() as p:
        #     print('Running Tests')
        #     ret = p.starmap(run_wrapper, [(i, *args) for i, args in enumerate(zip(ports, algs, tests))])

        portfolio = Portfolio(self._stocks, self._starting_cash, self._fee)
        algorithm = self._strategy(*tuple(), **algorithm_params or None)
        tests = [(prices, data, self._indicator_cache.get(i)) for i, (prices, data) in enumerate(zip(*self._precomp_prices))]

        ret = run_wrapper(0, portfolio, algorithm, tests)
        all_results = [Result(cash,  self._data.index, self._fee, self._stocks, (algorithm_params, indicator_params),  transactions=transactions) for cash, *transactions in [ret]]

        print(str(sum(all_results[1:], start=all_results[0])))

        return all_results

        # it = tqdm(iter(zipped), total=len(self._data)) if progressbar else iter(zipped)
        # print('Running Tests')
        # for params in it:
        #     algorithm.run_on_data(params, portfolio)
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
        # cash, longs, shorts = portfolio.history

        # res = Result(cash, longs, shorts, self._data.index, (algorithm_params, indicator_params), self._stocks, self._fee)
        # print(res)
        # print(portfolio.history)

class Result:

    def __init__(self, cash, time,  fee, stocks, params, transactions=None):
        self.params = params
        self.stocks = stocks
        self.stats = self.parse(self.stocks, *transactions) if transactions else None

        self.cash = cash
        self.fee = fee
        self.time_index = time


    def parse(self, stocks, longs, shorts):

        # time, stock, profit
        df = pd.DataFrame()

        for stock in stocks:
            l = [p for _,s,p in longs if s == stock] 
            s = [p for _,s,p in shorts if s == stock] 

            m_l = np.mean(l or [0]) 
            m_s = np.mean(s or [0]) 


            df[stock] = [
                        len(l) + len(s),   (m_l + m_s)/2,   np.std((l + s) or [0]), 
                        len(l),             m_l,            np.std(l or [0]),  
                        len(s),             m_s,            np.std(s or [0])
                        ]
        
        a_longs, a_shorts = [p for *_,p in longs], [p for *_,p in shorts]

        m_l = np.mean(a_longs or [0])
        m_s = np.mean(a_shorts or [0])
        
        df['Total'] = [
                    len(a_longs) + len(a_shorts),  (m_l + m_s)/2,   np.std((a_longs + a_shorts) or [0]), 
                    len(a_longs),                   m_l,            np.std(a_longs or [0]),  
                    len(a_shorts),                  m_s,            np.std(a_shorts or [0])
                    ]

        df.fillna(0, inplace=True)

        df.index = [f'{b}_{a}' for a,b in itertools.product(['trades', 'longs', 'shorts'], ["n", 'mean_per', 'std'])]
        

        return df
                

    def __str__(self):
        return f'{self.params[0]}\n{self.params[1]}\nStarting Balance:\t{self.cash[0]}\nFee:\t\t\t{self.fee}\n{self.stats}'


    def __add__(self, other):
            
        res = Result(self.cash, self.time_index,  self.fee, self.stocks, self.params, transactions=None)

        res.stats = (self.stats + other.stats)/2 if not other.stats is None else self.stats
        
        return res

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


