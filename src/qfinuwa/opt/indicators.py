import numpy as np
from itertools import product


class Indicators:

    def __init__(self, stocks, data):

        self._params = dict()
        self._stocks = stocks

        self._cache = dict()
        self._data = data

        self._L = len(list(self._data.values())[0])

        self._curr_indicators = None 
        self._default = None

        self._indicators_iterations = None



    # TODO
    
    
    @property
    def defaults(self):
        return self._default

    def set_default(self, indicators, strategy):

        defaults = strategy.defaults()['indicators']

        for indicator, params in defaults.items():
            defaults[indicator].update(indicators[indicator])

        for indicator, params in defaults.items():
            if not self._is_cached(indicator, params): 
                self.add(indicator, params, strategy)
        self._default = defaults
        

    def update_algorithm(self, algorithm):
        self._cache = dict()
        self._default = algorithm.defaults()['indicators']
        for indicator in (self._default):   
            self.add(indicator, self._default[indicator], algorithm)
    #
    def add(self, indicator, i_params, strategy):
        if self._is_cached(indicator, i_params):
            return

        i_params_tuple = self.params_to_hashable(i_params)

        if indicator not in self._cache:
            self._cache[indicator] = dict()

        indicator_functions = strategy.indicator_functions()
        self._cache[indicator][i_params_tuple] = {stock: indicator_functions[indicator](self._data[stock], **i_params) for stock in self._data}

    #
    def _is_cached(self, indicator, params):

        if indicator not in self._cache:
            return False

        return self.params_to_hashable(params) in self._cache[indicator]

    #
    def _get_indicator(self, indicator, params):

        if not self._is_cached(indicator, params):
            return None

        return self._cache[indicator][self.params_to_hashable(params)]

    #
    def params_to_hashable(self, params):
        return tuple(sorted([(p, v) for p, v in params.items()]))
        

    # we aren't using iterators here because this object needs to be a shared object
    def iterate(self, params):
        self._indicators = dict()
        for indicator, i_params in params.items():
            stock_values = self._get_indicator(indicator, i_params)
            if stock_values is None:
                raise ValueError(f'Indicator {indicator} with params {i_params} not found.')
            self._indicators[indicator] = np.stack([values for values in stock_values.values()], axis=1)
        
        self._curr_indicators = {stock: {indicator: None for indicator in params} for stock in self._stocks}  
        self._indexes = product(range(len(self._stocks)), self._indicators)
        self._L = len(self._indicators[list(self._indicators.keys())[0]])

    def __len__(self):
        return self._L

    def __iter__(self):


        if not self._default:
            raise ValueError(f'No default parameters found.')


        self._indicators_iterations = {indicator: np.stack(list(self._get_indicator(indicator, i_params).values()), axis=1) for indicator, i_params in self._default.items()}

        self._curr_indicators = {stock: {indicator: None for indicator in self._default} for stock in self._stocks}  

        self._indexes = product(range(len(self._stocks)), self._indicators_iterations)
        self._i = 0

        return self

    def __next__(self):

        if self._i >= len(self):
            raise ValueError(f'Index {self._i } out of range.')

        for s, indicator in self._indexes:  
            self._curr_indicators[self._stocks[s]][indicator] = self._indicators_iterations[indicator][:self._i, s]
        
        self._i += 1
        
        return self._curr_indicators
