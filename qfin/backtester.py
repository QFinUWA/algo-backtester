import itertools
from tqdm import tqdm
from .opt.portfolio import Portfolio
from .opt.stockdata import StockData
import pandas as pd
from multiprocessing import Pool
from functools import partial
import math
from time import time

class Backtester:

    def __init__(self, strategy, stocks, data=r'\data', tests=20, cash=1000, fee=0.001):

        self._strategy = strategy
        self._x = data
        self._data = StockData(stocks, data)
        self._stocks = stocks
        self._update_indicators = list()
        self._cash = cash
        self._fee = fee
        self._algorithm_params = dict()
        self._indicator_params = dict()
        self._analyser = Analyser()

    @property
    def fee(self):
        return self._fee

    @property
    def stocks(self):
        return self._data.stocks

    '''
    Marks indicators as needing to be updated.
    '''

    def update_indicators(self, only=None):

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
        to_update = {k: v for k, v in params.items(
        ) if k not in self._indicator_params or self._indicator_params.get(k, None) != v}

        if len(to_update) == 0:
            return

        self._data.add_indicators(self._strategy, to_update)
        self._indicator_params.update(params)

    def run_wrapper(self, alg_params):

        self.run(algorithm_params=alg_params, progressbar=False)

    '''
    TODO: Add paramter to only recalculate certrain indicators
    '''

    def backtest_strategies(self, strategy_params, indicator_params, multiprocessing=False):
        import copy
        self._data.remove_indicators()
        s = time.time()
        [copy.copy(self._data) for _ in tqdm(range(50))]
        print(time.time() -s )
        assert False
        # backtesting a range of instances (maybe this should be a separate function?)
        results = []
        # TODO: if not iterable, set exact to list of length 1
        # TODO: multiprocessing

        # get all combinations of algorithm paramters
        param, val = zip(*strategy_params.items())
        strategy_comb = [dict(zip(param, v)) for v in itertools.product(*val)]

        # precompute all indicators and store in dictionary
        indicator_maps = {indicator: dict() for indicator in indicator_params}
        # total_indicator_comb = 1
        len_indicator_comb = sum(len(values) for paramters in indicator_params.values() for values in paramters.values())     

        with tqdm(total=len_indicator_comb, desc="Precomputing indicator variants.") as bar:
            for indicator, paramters in indicator_params.items():
                
                param, val = zip(*paramters.items())

                permutations_dicts = [dict(zip(param, v))
                                for v in itertools.product(*val)]

                # total_indicator_comb *= len(permutations_dicts)

                for perm in permutations_dicts:
                    indicator_maps[indicator][tuple(perm.values())] = self._data.calc_indicator(self._strategy, indicator, perm)
                    bar.update(1)
            
        # get every combination of different indicators
        permutations_comb = [_ for _ in itertools.product( *indicator_maps.values())]
        combined_comb = itertools.product(strategy_comb, permutations_comb)

        '''
        define new function that
            - updates indicator params
            - creates new indicators
            - adds indicators to data explicitly
            - runs algorithm
            - returns results of run
        '''
        res = []
        for perm in permutations_comb:

            self._indicator_params.update({ind: dict(zip(indicator_params[ind].keys(), x)) for ind, x in zip(indicator_params.keys(), perm)})

            new_indicators = {i: indicator_maps[i][c] for i, c in zip(indicator_params.keys(), perm)}

            self._data.add_indicators_explicit(new_indicators)
            
            if multiprocessing:
                for alg_params in strategy_comb:
                    res.append(self.run(algorithm_params=alg_params, progressbar=False))
                continue

            # TODO add params to results
            with Pool(processes=2) as p:
                res = p.map(self.run_wrapper, [(self, strat) for strat in strategy_comb])

                # self.run(algorithm_params=strat, progressbar=False)
        
            print(res)

    '''
    Backtests the stored strategy. 
    '''

    def run(self, algorithm_params = None, indicator_params = None, progressbar=True):

        if bool(algorithm_params):
            if not isinstance(algorithm_params, dict):
                raise TypeError(f'algorithm_params must be of type dict, not {type(algorithm_params)}')
            self.set_algorithm_params(algorithm_params)

        
        if bool(indicator_params):
            if not isinstance(algorithm_params, dict):
                raise TypeError(f'indicator_params must be of type dict, not {type(indicator_params)}')
            self.set_indicator_params(indicator_params)

        algorithm = self._strategy(*tuple(), **self._algorithm_params or None)

        # TODO check instaniated

        # backtesting an instance of a strategy

        portfolio = Portfolio(self._stocks, self._cash,
                              self._fee, len(self._data))

        it = tqdm(iter(self._data)) if progressbar else iter(self._data)
        for curr_prices, all_prices in it:
            algorithm.run_on_data(curr_prices, all_prices, portfolio)
        # print(portfolio)

        ret = Result()
        df_ret = portfolio.history
        df_ret['time'] = pd.DatetimeIndex(self._data.index)
        ret.hist = df_ret

        ret.fee = self._fee
        ret.indicator_params = self._indicator_params.copy()
        ret.algorithm_params = self._algorithm_params.copy()
        ret.initial_balance = self._cash

        # self._analyser.parse_result(ret)
        return self._cash

        
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





