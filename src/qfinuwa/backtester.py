
from itertools import islice, product
from .opt._portfolio import Portfolio
from .opt._stockdata import StockData
import random
from .opt._result import SingleRunResult, MultiRunResult, ParameterSweepResult
from .strategy import Strategy
from .indicators import Indicators
from typing import Union
from itertools import islice
from typing import Union
from IPython import get_ipython

try:
    shell = get_ipython().__class__.__name__
    if shell in ['ZMQInteractiveShell']:
        from tqdm.notebook import tqdm as tqdm   # Jupyter notebook or qtconsole or Terminal running IPython  
    else:
         from tqdm import tqdm   
except NameError:
    from tqdm import tqdm      # Probably standard Python interpreter

    
class Backtester:


    def __init__(self, stocks: list, 
            strategy_class: Strategy, indicator_class: Indicators, 
            data: str=r'\data', days: Union[int , str] = 'all', 
            cash: float=1000, fee: float=0.001,
            progressbar=True):
        '''
        # Backteser
        A class for running a strategy on historical data. Once initialised, the data is precompiled
        for iterating. The parameters can be updated using the ``update_x`` and ``set_x`` functions.
        The strategy is run on the data by calling the either the ``run`` or ``run_grid_search`` method. 
        
        ## Parameters
        - ``stocks`` (``list``): A list of stock to run the strategy on.
        - ``strategy_class`` (``Strategy``): The strategy to run.
        - ``indicator_class`` (``Indicators``): The indicators to use in the strategy.
        - ``data`` (``str``): The path to the data folder.
        - ``days`` (``int`` or ``str``): The number of days to run the strategy on. 
        - ``cash`` (``float``): The starting cash balance.
        - ``fee`` (``float``): The fee to pay on each transaction.
        - ``progressbar`` (``bool``): Whether to show a progress bar when loading data.

        ## Properties
        - ``strategy_params`` (``dict``): The parameters of the strategy.
        - ``indicator_params`` (``dict``): The parameters of the indicators.
        - ``fee`` (``float``): The fee to pay on each transaction.
        - ``stocks`` (``list``): The stocks to run the strategy on.
        - ``days`` (``int``): The number of days to run the strategy on.
        - ``starting_balance`` (``float``): The starting cash balance.

        ## Returns
        ``None``

        ## Example
        ```python
        from qfinuwa import Backtester

        backtester = Backtester(['AAPL', 'GOOG'], data=r'\data', days=90, fee=0.01)
        ```

        '''
        # raise execption if strategy is not a subclass of Strategy
        if not issubclass(strategy_class, Strategy):
            raise ValueError('Strategy must be a subclass of Strategy')   
        self._strategy = strategy_class

        self._data = StockData(data, stocks=stocks, verbose=progressbar)
        self._precomp_prices = self._data.prices

        # raise expection if indiators is not a subclass of Indicators
        if not issubclass(indicator_class, Indicators):
            raise ValueError('Indicators must be a subclass of Indicators')
        
        self._indicators = indicator_class(self._data)

        self._fee = fee
        self._starting_balance = cash
        
        self._strategy_params = dict()

        self._days = days

        self._random = random

    #---------------[Properties]-----------------#
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
    def strategy_params(self):
        x = self._strategy.defaults()
        x.update(self._strategy_params)  
        return x
    
    @property
    def days(self):
        return self._days
    
    @property
    def starting_balance(self):
        return self._starting_balance
    
    #---------------[Public Methods]-----------------#
    def set_days(self, days: Union[int, str]) -> None:
        '''
        Sets the number of days to run the strategy on.
        If days is a string, it must be ``'all'`` and the strategy will be run on all available data.
        If days is an integer, ``n``, it must be a positive integer and the strategy will be run on the last ``n`` days.

        ## Parameters
        - ``days`` (``int`` or ``str``): The number of days to run the strategy on.

        ## Returns
        ``None``
        '''
        if isinstance(days, str) and days != 'all':
            raise ValueError('days must be an integer or "all"')
        
        if isinstance(days, int) and days < 0:
            raise ValueError('days must be a positive integer or "all"')
        
        self._days = days

    def set_starting_balance(self, balance: float) -> None:
        '''
        Sets the starting balance of the strategy.

        ## Parameters
        - ``balance`` (``float``): The starting cash balance.

        ## Returns
        ``None``

        '''
        if balance < 0:
            raise ValueError('balance must be a positive number')
        self._starting_balance = balance


    def set_indicator_params(self, params: dict) -> None:
        '''
        Sets the stored indicators.

        ## Parameters
        - ``indicator_class`` (``Indicator``): subclass of Indicators

        ## Returns
        ``None``
        '''
        self._indicators.update_parameters(params)

    def set_strategy(self, strategy_class: Strategy) -> None:
        '''
        Sets the stored strategy.

        ## Parameters
        - ``strategy_class`` (``Strategy``): subclass of Strategy

        ## Returns
        ``None``
        '''
        self._strategy = strategy_class

        if strategy_class.defaults().keys() - self.strategy_params.keys():
            print('! Strategy parameters changed: resetting to defaults !')
            self.strategy_params = strategy_class.defaults()
            
    def update_indicators(self, indicator_class: Indicators) -> None:
        '''
        Updates the stored indicators.

        ## Parameters
        - ``indicator_class`` (``Indicator``): subclass of Indicators

        ## Returns
        ``None``
        '''
        self._indicators = indicator_class(self._data)

    def set_strategy_params(self, params: dict) -> None:
        '''
        Sets the stored strategy.

        ## Parameters
        - ``strategy_class`` (``Strategy``): subclass of Strategy

        ## Returns
        ``None``
        '''

        if not self._strategy:
            raise ValueError('No strategy specified')
        self._strategy_params.update({k:v for k,v in params.items() if k in self._strategy.defaults()})

    def run(self, strategy_params: dict = None, indicator_params: dict = None, progressbar: bool=True, cv: int = 1, seed: int = None) -> MultiRunResult:
        '''
        Runs the strategy on a set of hyperparameters.

        ## Parameters
        - ``strategy_params`` (``dict``): The parameters of the strategy.
        - ``indicator_params`` (``dict``): The parameters of the indicators.
        - ``progressbar`` (``bool``): Whether to show a progress bar.
        - ``cv`` (``int``): The number of cross-validation folds to use.
        - ``seed`` (``int``): The seed to use for the random number generator.

        ## Returns
        result (``MultiRunResult``): The results of the strategy.
        '''

        if not self._strategy:
            raise ValueError('No strategy specified')

        if bool(strategy_params):
            if not isinstance(strategy_params, dict):
                raise TypeError(f'strategy_params must be of type dict, not {type(strategy_params)}')

            # fill in missing parameters with defaults
            alg_defaults = self._strategy.defaults()
            alg_defaults.update(strategy_params)
            strategy_params = alg_defaults
        else:
            strategy_params = self.strategy_params

        if bool(indicator_params):
            if not isinstance(indicator_params, dict):
                raise TypeError(f'indicator_params must be of type dict, not {type(indicator_params)}')
            self._indicators._add_parameters(indicator_params)
        else:
            indicator_params = self._indicators.params

        self._random.seed(seed or random.randint(0, 2**32))
        random_periods = self._get_random_periods(cv) 
        results = []

        # caclulate indicators 
        data = zip(*self._precomp_prices, self._indicators._iterate_params(indicator_params))

        desc = f'> Running backtest over {cv} sample{"s" if cv > 1 else ""} of {self._days} day{"s" if cv > 1 else ""}'
        for start, end in (tqdm(random_periods, desc = desc) if progressbar and cv > 1 else random_periods):
            portfolio = Portfolio(self.stocks, self._starting_balance, self._fee)
            if strategy_params:
                strategy = self._strategy(*tuple(), **strategy_params)
            else:
                strategy = self._strategy(*tuple())

            test = islice(data, start, end) 
        
            #---------[RUN THE ALGORITHM]---------#
            for params in (tqdm(test, desc=desc, total = end-start, mininterval=0.5) if progressbar and cv == 1 else test):
                strategy.run_on_data(params, portfolio)
            cash, longs, shorts = portfolio.wrap_up()
            to_add = strategy.on_finish()
            results.append(SingleRunResult(self.stocks, self._data, self._data.index, (start, end), cash, longs, shorts, to_add ))
            #-------------------------------------#

        return MultiRunResult((strategy_params, indicator_params), results)
    
    def run_grid_search(self, strategy_params: dict = None, indicator_params: dict = None, cv: int = 1, seed: int =None) -> ParameterSweepResult:
        '''
        Runs a grid search over a set of hyperparameters.

        ## Parameters
        - ``strategy_params`` (``dict``): The parameters of the strategy.
        - ``indicator_params`` (``dict``): The parameters of the indicators.
        - ``cv`` (``int``): The number of cross-validation folds to use.
        - ``seed`` (``int``): The seed to use for the random number generator.

        ## Returns
        result (``ParameterSweepResult``): The results of the strategy.
        '''
        # get all combinations of strategy paramters
        # ----[strategy params]----
        strategy_params = strategy_params or dict()

        if strategy_params.keys() - self.strategy_params.keys():
            raise ValueError('Invalid strategy parameters')

        default_strategy_params = {**self.strategy_params, **strategy_params}
        param, val = zip(*default_strategy_params.items())
        val = map(lambda v: v if isinstance(v, list) else [v], val)
        strategy_params_list = [dict(zip(param, v)) for v in product(*val)]

        # ----[indicator params]----
        
        indicator_params = indicator_params or dict()
        indicator_params_list = self._indicators._get_permutations(indicator_params)


        print('> Backtesting the across the following ranges:')
        print('Agorithm Parameters', default_strategy_params)
        print('Indicator Parameters', self._indicators._fill_in_defaults(indicator_params))

        # run
        seed = seed or self._random.randint(0, 2**32)
        res = []
        print('Running backtests...')
        for alg_params, ind_params in tqdm(product(strategy_params_list, indicator_params_list), total=len(strategy_params_list) * len(indicator_params_list), desc=f"Running paramter sweep (cv={cv})"):
            res.append(self.run(strategy_params=alg_params, indicator_params=ind_params, cv=cv, seed=seed, progressbar=False))
        
        return ParameterSweepResult(res)
    
    #---------------[Private Methods]-----------------#
    def _get_random_periods(self, n: int) -> list:

        if self._days == 'all':
            return [(0, len(self._data)) for _ in range(n)]

        days = self._data.index.dt.to_period('D').drop_duplicates()
    
        s_is = self._random.sample(range(len(days) - self._days), n)

        starts = (str(days.iloc[s_i]) for s_i in s_is)
        ends = (str(days.iloc[s_i+self._days]) for s_i in s_is)

        return [(self._data._index[self._data._index >= start].index[0], self._data._index[self._data._index < end].index[-1]) for start, end in zip(starts, ends)]
    

    #---------------[Internal Methods]-----------------#
    def __str__(self):
        return  f'Backtester:\n' + \
                f'- Strategy: {self._strategy.__name__}\n' + \
                f'\t- Params: {self.strategy_params}\n' + \
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




