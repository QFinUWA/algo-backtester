import itertools
from tqdm import tqdm
from .opt.portfolio import Portfolio
from .opt.stockdata import StockData


class Backtester:

    def __init__(self, strategy, stocks, data=r'\data', tests=20, cash=1000, fee=0.001):

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

    '''
    TODO: Add paramter to only recalculate certrain indicators
    '''

    def backtest_strategies(self, strategy_params, indicator_params):
        
        # backtesting a range of instances (maybe this should be a separate function?)
        results = []
        # TODO: if not iterable, set exact to list of length 1
        # TODO: multiprocessing

        # get all combinations of algorithm paramters
        param, val = zip(*strategy_params.items())
        strategy_comb = [dict(zip(param, v)) for v in itertools.product(*val)]

        # precompute all indicators and store in dictionary
        indicator_maps = {indicator: dict() for indicator in indicator_params}
        total_indicator_comb = 1
        for indicator, paramters in indicator_params.items():
            
            param, val = zip(*paramters.items())

            permutations_dicts = [dict(zip(param, v))
                              for v in itertools.product(*val)]

            total_indicator_comb *= len(permutations_dicts)

            for perm in permutations_dicts:
                indicator_maps[indicator][tuple(perm.values())] = self._data.calc_indicator(self._strategy, indicator, perm)
        
        # get every combination of different indicators
        with tqdm(total=total_indicator_comb*len(strategy_comb)) as it:
            for perm in itertools.product(*indicator_maps.values()):
                
                new_indicators = {i: indicator_maps[i][c]for i, c in zip(indicator_params.keys(), perm)}

                self._data.add_indicators_explicit(new_indicators)

                # for every combination of algorithm parameters
                for strat in strategy_comb:
                    # TODO add params to results
                    results.append(self.run(algorithm_params=strat, progressbar=False))
                    it.update(1)

        
        return results
       
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
        hist = portfolio.history.set_index(self._data.index)

        return hist