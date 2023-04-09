
from itertools import islice, product
from .opt._portfolio import Portfolio
from .opt._stockdata import StockData
import random
from .opt._result import SingleRunResult, MultiRunResult, ParameterSweepResult
from .strategy import Strategy
from .indicators import Indicators
from typing import Union
from itertools import islice, tee
import datetime
from dateutil import parser
import numpy as np

# from IPython import get_ipython
# try:
#     shell = get_ipython().__class__.__name__
#     if shell in ['ZMQInteractiveShell']:
#         from tqdm.notebook import tqdm as tqdm   # Jupyter notebook or qtconsole or Terminal running IPython  
#     else:
#          from tqdm import tqdm   
# except NameError:
#     from tqdm import tqdm      # Probably standard Python interpreter
from tqdm import tqdm

class _StrategyModifier:
    '''
    The ONLY reason this class exists is so the same notation can be used to update both the 
    strategy parameters and the indicator parameters.
    '''

    def __init__(self, strategy_class: Strategy):
        self._strategy = strategy_class
        self.name = strategy_class.__name__
        self._params = dict()
    
    @property
    def params(self):
        x = self._strategy.defaults()
        x.update(self._params)  
        return x
    
    @property
    def defaults(self):
        return self._strategy.defaults()
    
    def update(self, strategy_class):
        if strategy_class.defaults().keys() - self.params.keys():
            print('! Strategy parameters changed: resetting to defaults !')
            self._params = dict()
        self._strategy = strategy_class
        self.name = strategy_class.__name__

    def update_params(self, params: dict) -> None:
        '''
        Sets the stored strategy parameters.

        ## Parameters
        - ``params`` (``dict``): updates to be make to the strategy.

        ## Returns
        ``None``
        '''

        # if not self._strategy:
        #     raise ValueError('No strategy specified')
        self._params.update({k:v for k,v in params.items() if k in self.defaults})


class Backtester:

    def __init__(self,  strategy_class: Strategy, indicator_class: Indicators, 
            stocks: list, 
            data_folder: str, days: Union[int , str] = 'all', 
            delta_limits:  Union[int , dict]=10000, fee: float=0.0,
            progressbar=True):
        '''
        # Backteser
        A class for running a strategy on historical data. Once initialised, the data is precompiled
        for iterating. The parameters can be updated using the ``update_x`` and ``set_x`` functions.
        The strategy is run on the data by calling the either the ``run`` or ``run_grid_search`` method. 
        
        ## Parameters
        - ``strategy_class`` (``Strategy``): The strategy to run.
        - ``indicator_class`` (``Indicators``): The indicators to use in the strategy.
        - ``stocks`` (``list``): A list of stock to run the strategy on.
        - ``data_folder`` (``str``): The path to the data folder.
        - ``days`` (``int`` or ``str``): The number of days to run the strategy on. 
        - ``delta_limit`` (``int`` or ``dict``): The general delta limit, or a dictionary of delta limits per instrument.
        - ``fee`` (``float``): The fee to pay on each transaction.
        - ``progressbar`` (``bool``): Whether to show a progress bar when loading data.

        ## Properties
        - ``strategy_params`` (``dict``): The parameters of the strategy.
        - ``indicator_params`` (``dict``): The parameters of the indicators.
        - ``fee`` (``float``): The fee to pay on each transaction.
        - ``stocks`` (``list``): The stocks to run the strategy on.
        - ``days`` (``int``): The number of days to run the strategy on.
        - ``starting_cash`` (``float``): The starting cash balance.

        ## Returns
        ``None``

        ## Example
        ```python
        from qfinuwa import Backtester

        backtester = Backtester(CustomStrategy, CustomIndicators, 
                                data=r'\data', days=90, 
                                delta_limit=800, fee=0.01)
        ```

        '''
        # raise execption if strategy is not a subclass of Strategy
        if not issubclass(strategy_class, Strategy):
            raise ValueError('Strategy must be a subclass of Strategy')  
         
        self._strategy_wrapper = _StrategyModifier(strategy_class)
        # self._strategy = strategy_class

        self._data = StockData(data_folder, stocks=stocks, verbose=progressbar)
        self._precomp_prices = self._data.prices

        # raise expection if indiators is not a subclass of Indicators
        if not issubclass(indicator_class, Indicators):
            raise ValueError('Indicators must be a subclass of Indicators')
        

        self._indicators = indicator_class(data=self._data)

        self._fee = fee
        # self._starting_cash = starting_cash  
        
            
        if isinstance(delta_limits, int):
            self._delta_limits = {stock: delta_limits for stock in self.stocks}
        elif isinstance(delta_limits, dict):
            if set(delta_limits.keys()) ^ set(self.stocks):
                raise ValueError(f'delta_limit either contains unknown stocks or doesn\'t include all stocks')
            if not all(map(lambda x: isinstance(int, x) and x > 0, delta_limits.values)):
                raise ValueError(f'delta_limit includes either non int or negative value')
        else:
            self._delta_limits = delta_limits

        self._days = days

        self._random = random

    #---------------[Properties]-----------------#
    @property
    def strategy(self):
        return self._strategy_wrapper
    
    @strategy.setter
    def strategy(self, strategy_class):
        self._strategy_wrapper.update(strategy_class)


    @property
    def indicator_params(self):
        return self._indicators.params
            
    @property
    def stocks(self):
        return self._data.stocks
    
    @property
    def fee(self):
        return self._fee
    
    @fee.setter
    def fee(self, fee):
        if fee < 0:
            raise ValueError('fee must be a positive number')
        self._fee = fee
    
    @property
    def days(self):
        return self._days
    
    @days.setter
    def days(self, days):
        if isinstance(days, str) and days != 'all':
            raise ValueError('days must be an integer or "all"')
        
        if isinstance(days, int) and days < 0:
            raise ValueError('days must be a positive integer or "all"')
        
        self._days = days
    
    # @property
    # def starting_cash(self):
    #     return self._starting_cash

    
    # @starting_cash.setter
    # def starting_cash(self, starting_cash):
    #     if starting_cash < 0:
    #         raise ValueError('starting_cash must be a positive number')
    #     self._starting_cash = starting_cash

    @property
    def delta_limits(self):
        return self._delta_limits
    
    @delta_limits.setter
    def delta_limits(self, delta_limit):

        if isinstance(delta_limit, dict):
            if set(delta_limit.keys()) ^ set(self.stocks):
                raise ValueError(f'delta_limit either contains unknown stocks or doesn\'t include all stocks')
            if not all(map(lambda x: isinstance(x, int) and x > 0, delta_limit.values())):
                raise ValueError(f'delta_limit includes either non int or negative value')
            self._delta_limits = delta_limit
        elif isinstance(delta_limit, int):
            self._delta_limits = {stock: delta_limit for stock in self.stocks}

        
    
    @property
    def indicators(self):
        return self._indicators
    
    @indicators.setter
    def indicators(self, indicator_class: Indicators) -> None:
        '''
        Updates the stored indicators.

        ## Parameters
        - ``indicator_class`` (``Indicator``): subclass of Indicators

        ## Returns
        ``None``
        '''
        self._indicators = indicator_class(self._data)

    @property
    def _strategy(self):
        '''
        For internal use only.
        '''
        return self._strategy_wrapper._strategy
    
    @property
    def date_range(self):
        return self._data.date_range
    
    #---------------[Public Methods]-----------------#
       
    def run(self, strategy_params: dict = None, indicator_params: dict = None, 
            cv: int = 1, seed: int = None, start_dates: list = None,
            progressbar: bool=True) -> MultiRunResult:
        '''
        Runs the strategy on a set of hyperparameters.

        ## Parameters
        - ``strategy_params`` (``dict``): The parameters of the strategy.
        - ``indicator_params`` (``dict``): The parameters of the indicators.
        - ``cv`` (``int``): The number of cross-validation folds to use.
        - ``seed`` (``int``): The seed to use for the random number generator.
        - ``start_dates`` (``list``): List of start dates to test on.
        - ``progressbar`` (``bool``): Whether to show a progress bar.

        ## Returns
        result (``MultiRunResult``): The results of the strategy.
        '''
        if bool(strategy_params):
            if not isinstance(strategy_params, dict):
                raise TypeError(f'strategy_params must be of type dict, not {type(strategy_params)}')

            # fill in missing parameters with defaults
            alg_defaults = self.strategy.defaults
            alg_defaults.update(strategy_params)
            strategy_params = alg_defaults
        else:
            strategy_params = self.strategy.params
        if bool(indicator_params):
            if not isinstance(indicator_params, dict):
                raise TypeError(f'indicator_params must be of type dict, not {type(indicator_params)}')
            self._indicators._add_parameters(indicator_params)
        else:
            indicator_params = self._indicators.params

        self._random.seed(seed or random.randint(0, 2**32))
        if start_dates is not None:
            if not isinstance(start_dates, list):
                raise ValueError('start_dates must be a list')
            
            cv = len(start_dates)

            test_periods = self._get_periods(start_dates)
        else:
            test_periods = self._get_random_periods(cv) 
        results = []

        # caclulate indicators 
        data_tees = tee(self._precomp_prices[0], cv), \
                    tee(self._precomp_prices[1], cv), \
                    self._indicators._iterate_params(indicator_params, copies=cv)
        test_iterator = zip(*data_tees, test_periods)

        days_format = f'{self._days} day{"s" if isinstance(self._days, str) or self._days > 1 else ""}'

        desc = f'> Running backtest over {cv} sample{"s" if cv > 1 else ""} of {days_format}'
        for *data, (start, end) in (tqdm(test_iterator, desc = desc, total = cv) if progressbar and cv > 1 else test_iterator):
            
            portfolio = Portfolio(self.stocks, self._delta_limits, self._fee)
            if strategy_params:
                strategy = self._strategy(*tuple(), **strategy_params)
            else:
                strategy = self._strategy(*tuple())

            test = islice(zip(*data), start, end) 
        
            #---------[RUN THE ALGORITHM]---------#
            for test_data in (tqdm(test, desc=desc, total = end-start, mininterval=0.5) if progressbar and cv == 1 else test):
                strategy.run_on_data(test_data, portfolio)
            value, trades = portfolio.wrap_up()
            on_finish = strategy.on_finish()

            results.append(SingleRunResult(self.stocks, self._data, self._data.index, (start, end), value, trades, on_finish ))
            #-------------------------------------#

        return MultiRunResult((strategy_params, indicator_params), results)
    
    def run_grid_search(self, strategy_params: dict = None, indicator_params: dict = None, 
                        cv: int = 1, seed: int =None, start_dates: list = None) -> ParameterSweepResult:
        '''
        Runs a grid search over a set of hyperparameters.

        ## Parameters
        - ``strategy_params`` (``dict``): The parameters of the strategy.
        - ``indicator_params`` (``dict``): The parameters of the indicators.
        - ``cv`` (``int``): The number of cross-validation folds to use.
        - ``seed`` (``int``): The seed to use for the random number generator.
        - ``start_dates`` (``list``): List of start dates to test on.

        ## Returns
        result (``ParameterSweepResult``): The results of the strategy.
        '''
        # get all combinations of strategy paramters
        # ----[strategy params]----
        strategy_params = strategy_params or dict()

        if strategy_params.keys() - self._strategy_wrapper.params.keys():
            raise ValueError('Invalid strategy parameters')

        default_strategy_params = {**self._strategy_wrapper.params, **strategy_params}
        param, val = zip(*default_strategy_params.items())
        val = map(lambda v: v if isinstance(v, list) else [v], val)
        strategy_params_list = [dict(zip(param, v)) for v in product(*val)]

        # ----[indicator params]----
        
        indicator_params = indicator_params or dict()
        indicator_params_list = self._indicators._get_permutations(indicator_params)

        print('> Backtesting the across the following ranges:')
        print('Agorithm Parameters', default_strategy_params)
        print('Indicator Parameters', self._indicators._fill_in_params(indicator_params))

        # run
        seed = seed or self._random.randint(0, 2**32)
                
        # print('get periods')
        if start_dates is not None:
            if not isinstance(start_dates, list):
                raise ValueError('start_dates must be a list')
            
            cv = len(start_dates)

            test_periods = self._get_periods(start_dates)
        else:
            # print(cv)
            test_periods = self._get_random_periods(cv) 
        total = len(strategy_params_list) * len(indicator_params_list)
        res = [None for _ in range(total)]

        for i, (alg_params, ind_params) in tqdm(enumerate(list(product(strategy_params_list, indicator_params_list))), total=total, desc=f"Running paramter sweep (cv={cv})"):
            res[i] = self.run(strategy_params=alg_params, indicator_params=ind_params, cv=cv, seed=seed, progressbar=False, start_dates=test_periods)
        
        return ParameterSweepResult(res, (default_strategy_params, self._indicators._fill_in_params(indicator_params)))
    
    #---------------[Private Methods]-----------------#
    def _get_random_periods(self, n: int) -> list:

        if self._days == 'all':
            return [(0, len(self._data)) for _ in range(n)]

        days = self._data.index.dt.to_period('D').drop_duplicates()
    
        s_is = self._random.sample(range(len(days) - self._days), n)
        
        starts = [days.iloc[s_i].strftime("%d/%m/%Y") for s_i in s_is]

        return self._get_periods(starts)
    
        ends = (str(days.iloc[s_i+self._days]) for s_i in s_is)

        return [(self._data._index[self._data._index >= start].index[0], self._data._index[self._data._index < end].index[-1]) for start, end in zip(starts, ends)]
    
    def _get_periods(self, start_dates: list) -> list:
        if all(map(lambda d: isinstance(d[0], np.int64) and isinstance(d[1], np.int64), start_dates)):
            return start_dates

        d = datetime.timedelta(days = self._days)
        dt_starts = (parser.parse(s, dayfirst=True) for s in start_dates)
        # dt_starts = [datetime.datetime(date) for date in parsed]

        # dt_starts = start_dates
        periods = [(s, s+d) for s in dt_starts]
        index_start, index_end = self._data.date_range
        for s,e in periods:
            if s + datetime.timedelta(days = 1) < index_start or e > index_end:
                raise IndexError(f'Date range {s} -> {e} out of bounds: Please ensure start_date and (start_date + days) are in range.')
        return  [(self._data._index[self._data._index >= str(s)].index[0], self._data._index[self._data._index < str(e)].index[-1]) for s, e in periods]


    #---------------[Internal Methods]-----------------#
    def __str__(self):
        return  f'Backtester:\n' + \
                f'- Strategy: {self.strategy.name}\n' + \
                f'\t- Params: {self.strategy.params}\n' + \
                f'- Indicators: {self._indicators.__class__.__name__}\n' + \
                f'\t- Params: {self._indicators.params}\n' + \
                f'\t- SingleIndicators: {self._indicators._singles}\n' \
                f'\t- MultiIndicators: {self._indicators._multis}\n' \
                f'- Stocks: {self.stocks}\n' + \
                f'- Fee {self.fee}\n' + \
                f'- delta_limit: {self.delta_limits}\n' + \
                f'- Days: {self._days}\n'
                # f'\t- Indicator Groups: {self._indicators.groups}\n' + \
    
    def __repr__(self):
        return self.__str__()




