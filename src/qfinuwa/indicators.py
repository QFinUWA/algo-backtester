
from functools import wraps
from inspect import signature, getmembers, Parameter
from itertools import product
from collections import defaultdict
from numpy import array
from .opt._stockdata import StockData

class Indicators:

    def __init__(self, data: str=None):

        '''
        # Indicators Base Class

        This is the base class for all indicators. It is not meant to be used directly.

        To create a custom indicator, create a function that takes in a data and returns a dictionary of indicator values.

        In all cases, the input data will be a pandas dataframe with the following columns: ``open``, ``high``, ``low``, ``close``, ``volume``.

        There are two classes of indicators: single and multi. 
        

        ## Single Indicators
        Given a dictionary of stocks and their data, return a dictionary of of indicator names and values.

        ### Example input and output
        ```python
        input = {'AAPL': pd.Dataframe({'close': [1, 2, 3, ...], 'volume': [100, 200, 300, ...], ...}), 
                 'MSFT': pd.Dataframe({'close': [4, 5, 6, ...], 'volume': [400, 500, 600, ...], ...}), ...}
        output = {'added_volume': [5, 7, 9, ...], 'constant_0': [0,0,0 ...], ...},
        ```

        ## Multi Indicators 
        Given a sinlge arbitary stock's data, return a dictionary of of indicator names and values.

        ### Example input and output
        ```python
        input = pd.Dataframe({'close': [1, 2, 3, ...], 'volume': [100, 200, 300, ...], ...})
        output = {'double_close': [2, 4, 6, ...], 'triple_volume': [300, 600, 900, ...], ...}
        ```

        ## Indicators in ``on_data``

        Your indicators will be passed into ``on_data`` as a dictionary of indicator names and values.

        For your ``SingleIndicators``, the dictionary will be of the form 
        ```python
        indicators["single_indicatorA"] =  np.array
        indicators["single_indicatorB"] =  np.array
        ```

        For your ``MultiIndicators``, the dictionary will be of the form 
        ```py
        indicators["multi_indicatorA"]: {'stockA': np.array, 'stockB': np.array, ... }
        indicators["multi_indicatorB"]: {'stockB': np.array, 'stockB': np.array, ... }
        ```

        ## Hyperparameters

        You can define hyperparameters for each indicator by adding them as keyword arguments to the indicator function.

        The default values will be used when ``backtester`` is created. You can then update those values by calling
        ``backtester.update_params``.

        Additionally you can supply a range of values for each hyperparameter. The ``backtester`` will then run the strategy
        for every combination of hyperparameters (``run_grid_search``).

        Any time you update the hyperparameters, the indicators will be recalculated and cached (they will only be calucated once).

        ## Example 
        class MyIndicators(Indicators):

        ```python
            @Indicators.MultiIndicator
            def sum_of_volumes(self, stock_df, mult = 1):
                return {'volsum': mult*sum(stock_df[stock]['volume'] for stock in stock_df)}
            
            @Indicators.SingleIndicator
            def bollingers(self, df, lookback = 20, n_std = 3):
                
                tp = (df['close'] + df['low'] + df['high']) / 3     # Calculate Typical Price
                matp = tp.rolling(lookback).mean()                  # Calculate Moving Average of Typical Price
                std = tp.rolling(lookback).std()                    # Calculate Standard Deviation
                
                upper = matp + n_std * std                          # Calculate Upper Bollinger Band
                lower = matp - n_std * std                          # Calculate Lower Bollinger Band
                return {'upper_bollinger': upper, 'lower_bollinger': lower}
        ```
        '''
        self._NULL_STOCK = '.'
        self.params = self.defaults

        if data is None:
            stockdata = StockData()
            return
        elif isinstance(data, str):
            stockdata = StockData(data_folder=data)
        elif isinstance(data, StockData):
            stockdata = data
        else:
            raise TypeError(f"Expected data to be of type str or StockData, got {type(data)} instead.")

        self._data = stockdata._stock_df
        self._index = stockdata._index
        self._L = len(stockdata)
        self._cache = dict()
        self._funcn_to_indicator_map = dict()
        self._add_parameters(self.params)

    #---------------[Class Methods]-----------------#
    @classmethod
    def SingleIndicator(cls, func):
        @wraps(func)
        def wrapper_func(*_args, **_kwargs):
            return func(*_args, **_kwargs)
        wrapper_func.SingleIndicator = True
        return wrapper_func
    
    @classmethod
    def MultiIndicator(cls, func):
        @wraps(func)
        def wrapper_func(*_args, **_kwargs):
            return func(*_args, **_kwargs)
        wrapper_func.MultiIndicator = True
        return wrapper_func
    
    #---------------[Properties]-----------------#
    @property
    def names(self):
        return sorted(sum((v for v in self._funcn_to_indicator_map.values()), start = []))

    @property
    def groups(self):
        return sorted(list(self._funcn_to_indicator_map.keys()))

    @property
    def _singles(self):
        return sorted(sum((v for k,v in self._funcn_to_indicator_map.items() if not self._is_multi(k)), start = []))
    
    @property
    def _multis(self):
        return sorted(sum((v for k,v in self._funcn_to_indicator_map.items() if self._is_multi(k)), start = []))
    
    @property
    def _indicator_functions(self):
        # TODO: filter by only functions
        cls = type(self)
    
        return {k: v for k, v in getmembers(cls)
                if callable(v) 
                and any(map(lambda x: hasattr(getattr(cls, k), x),  ['SingleIndicator', 'MultiIndicator']))} 
    @property
    def defaults(self):
        
        def get_defaults(func): 
            return {
                k: v.default
                for k, v in signature(func).parameters.items()
                if v.default is not Parameter.empty
            }
       
        return {name: get_defaults(function) for name, function in self._indicator_functions.items()}

    @property
    def _stocks(self):
        return list(self._data.keys())
    
    @property
    def index(self):
        return self._index

    #---------------[Public Methods]-----------------#
    def values(self, params: dict=None) -> dict:
        '''
        Return a dictionary of indicator names and values.

        ## Parameters
        - ``params`` (``dict``): The parameters to evaluate the indicators with. If ``None``, the default parameters will be used.
        
        ## Returns
        - ``dict``: A dictionary of indicator names and values.
        '''
        if len(self) == 0: 
            raise ValueError('No data to calculate indicators on. See __init__ docstring.')

        if params is None:
            params = self.params

        params = self._fill_in_params(params)
        self._add_parameters(params)

        # params maps function name to parameters
        vals = {}
        for funcn, indicators in self._funcn_to_indicator_map.items():
            for indicator in indicators:
                cached = self._get_cached(funcn, params[funcn], indicator)
                vals[indicator] = cached.get(self._NULL_STOCK, cached)
               
        return vals

    def update_params(self, params: dict) -> None:
        '''
        Update the parameters for the indicators.

        ## Parameters
        - ``params`` (``dict``): The parameters to evaluate the indicators with.

        ## Returns
        ``None``
        '''
        self._raise_invalid_params(params)
            
        self.params = self._fill_in_params(params)
        
        self._add_parameters(self.params)
        
    #---------------[Private Methods]-----------------#

    def _is_multi(self, indicator_function_name):
        if indicator_function_name not in self._indicator_functions:
            raise ValueError(f'Invalid indicator function name: {indicator_function_name}')
        return hasattr(getattr(type(self), indicator_function_name), 'MultiIndicator')

    def _fill_in_params(self, params):
        curr_params = {k: {k1:v1 for k1, v1 in v.items()} for k,v in self.params.items()}
        for indicator in params:   
            curr_params[indicator].update(params[indicator])
        return curr_params

    
    def _raise_invalid_params(self, params):
        defaults = self.defaults

        if params.keys() - defaults.keys():
            raise ValueError(f'Indicator group(s) not found: {params.keys() - defaults.keys()}')

        for func_name, f_params in params.items():
            if f_params.keys() - defaults[func_name].keys():
                raise ValueError(f'Indicator(s) not found in {func_name}: {f_params.keys() - defaults[func_name].keys()}')

    def _add_parameters(self, params):

        self._raise_invalid_params(params)

        for func_name, f_params in params.items():
            if func_name not in self._indicator_functions:
                raise ValueError(f'Indicator function {func_name} not found')

            self._add_indicator(func_name, self._indicator_functions[func_name], f_params) 


    def _add_indicator(self, func_name, func, params = None):
        
        if params is None:
            params = self.defaults[func_name]

        if self._is_cached(func_name, params):
            return
        
        to_cache = dict()
        for stock, data in (self._data.items() if self._is_multi(func_name) else [(self._NULL_STOCK, self._data)]):

            out = func(self, data, **params)
            if not isinstance(out, dict):
                raise ValueError(f'Indicator function {func_name} must return a dict')

            self._funcn_to_indicator_map[func_name] = sorted(list(out.keys()))
    
            for indicator, value in out.items():
                if indicator not in to_cache:
                    to_cache[indicator] = dict()
                to_cache[indicator].update({stock: value}) 

        self._cache_indicator(func_name, params, to_cache)

    def _get_permutations(self, funcn_to_params):

        self._raise_invalid_params(funcn_to_params)
        
        funcn_to_params = self._fill_in_params(funcn_to_params)

        combinations = defaultdict(list)

        for indicator, paramters in funcn_to_params.items():
            
            param, val = zip(*paramters.items())

            val = map(lambda v: v if isinstance(v, list) else [v], val)

            permutations_dicts = [dict(zip(param, v))
                            for v in product(*val)]

            for perm in permutations_dicts:                
                self._add_indicator(indicator, self._indicator_functions[indicator], perm)
                combinations[indicator].append(perm)

        # get every combination of different indicators
        every_combination =  [dict(zip(combinations.keys(), c)) for c in product(*combinations.values())]

        return every_combination

    def _iterate_params(self, params=None, copies=None):

        if params is None:
            params = self.params

        params = self._fill_in_params(params)
        self._add_parameters(params)

        # params maps function name to parameters
        self._indicators_iterations = {indicator: array(list(self._get_cached(funcn, params[funcn], indicator).values())) for funcn, indicators in self._funcn_to_indicator_map.items() for indicator in indicators}
        if copies is None:
            self.__iter__()
        # TODO: needlessly recreating iterator - could we just reset iterator related fields
        #       and iterate again? maybe a modulo type situation?
        return tuple(self.__iter__() for _ in range(copies))
    
    #---------[CACHE]---------#
    def _hashable(self, function_name, params):
        return (function_name, tuple(sorted(params.items())))

    def _cache_indicator(self, function_name, params, values):
        key = self._hashable(function_name, params)
        self._cache[key] = values
        return

    def _is_cached(self, function_name, params):
        return self._hashable(function_name, params) in self._cache

    def _get_cached(self, function_name, params, indicator):

        if not self._is_cached(function_name, params):
            return None
        
        key = self._hashable(function_name, params)
        return self._cache[key][indicator]

    #---------[/CACHE]---------#       
    
    #---------------[Internal Methods]-----------------#
    def __iter__(self):
        self._iterate_indicators = {indicator: {stock: None for stock in self._stocks} for indicator in self._multis}
        self._iterate_indicators.update({indicator: None for indicator in self._singles})

        self._indexes_multis = list(product(self._multis, range(len(self._stocks))))
        self._indexes_singles = self._singles
        self._i = 1
        return self

    def __next__(self):
        if self._i > len(self):
            self._indicators_iterations = None
            self._iterate_indicators = None
            self._indexes_multis = None
            self._indexes_singles = None
            self._i = None
            raise StopIteration(f'Index {self._i } out of range.')

        for indicator, s in self._indexes_multis: 
            self._iterate_indicators[indicator][self._stocks[s]] = self._indicators_iterations[indicator][s, :self._i]

        for indicator in self._indexes_singles:
            self._iterate_indicators[indicator] = self._indicators_iterations[indicator][0, :self._i]
        
        self._i += 1
        return self._iterate_indicators

    def __len__(self):
        return self._L