import itertools
from tqdm import tqdm
from .opt.portfolio import Portfolio
from .opt.stockdata import StockData
import pandas as pd
from multiprocessing import Pool
from functools import partial
import math
from time import time
import collections
from .opt.indicator import Indicators

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
        alg_params, ind_params = args
        return self.run(algorithm_params = alg_params, indicator_params = ind_params, progressbar=False)


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

        # run
        if not multiprocessing:
            res = []
            for alg_params, ind_params in itertools.product(strategy_comb, trials):
                res.append(self.run(algorithm_params=alg_params, indicator_params=ind_params, progressbar=False))
        else:
            with Pool(processes=1) as p:
                res = p.map(self.run_wrapper, [(alg_params, ind_params) for alg_params, ind_params in itertools.product(strategy_comb, trials)])

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

        zipped = zip(self._data, indicators)
        it = tqdm(iter(zipped), total = len(self._data)) if progressbar else iter(zipped)
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

        # self._analyser.parse_result(ret)
        return portfolio.cash

        
class Analyser:

    def __init__(self):
        self._i = 0
        return

    def parse_result(self, result):


        # store in hdf5 file format
        with pd.HDFStore(f'del/{self._i:02}.hdf5') as store:
            store.put('results', result.hist)
            store.get_storer('results').attrs.metadata = {"fee": result.fee, 
                                                        "indicator_params": result.indicator_params, 
                                                        "algorithm_params": result.algorithm_params,
                                                        "initial_balance": result.initial_balance,
                                                        }
            self._i += 1

class Result:

    def __init__(self):
        self.indicator_params = None
        self.algorithm_params = None
        self.hist = None
        self.fee = None
        self.initial_balance = None

    def __str__(self):
        return f'{self.indicator_params}\n{self.algorithm_params}\n{self.fee}\n{self.initial_balance}'





