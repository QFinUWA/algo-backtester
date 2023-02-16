import numpy as np
from itertools import product


class Indicators:

    def __init__(self, stocks, data):

        self._params = dict()
        self._stocks = stocks

        self._cache = dict()
        self._data = data

        self._L = len(list(self._data.values())[0])

        self._curr_indicator = {} 
        self._default = None

    # TODO

    @property
    def curr_indicators(self):   

        return self._fill_in_defaults(self._curr_indicator)
    
    
    def _fill_in_defaults(self, params):

        if not self._default:
            raise ValueError('No default indicators specified, try calling update_algorithm')

        defaults = {k:v for k,v in self._default.items()}
        for indicator in defaults:   
            defaults[indicator].update(params.get(indicator, {}))
        return defaults
  

    def set_indicator(self, indicators, strategy):
        
        indicators = self._fill_in_defaults(indicators)

        # print(defaults)
        for indicator, params in indicators.items():
            if not self._is_cached(indicator, params): 
                self.add(indicator, params, strategy)

        self._curr_indicator = indicators
        

    def update_algorithm(self, algorithm):
        self._cache = dict()
        self._default = algorithm.defaults()['indicators']
        self._curr_indicator = {}
        for indicator in self._default:   
            self._curr_indicator[indicator] = {}
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
    def iterate(self, params=None):

        if self._default is None:
            raise ValueError(f'No default indicator parameters found.')
        
        params = self._curr_indicator if params is None else self._fill_in_defaults(params)

        self._indicators = dict()
        for indicator, i_params in params.items():
            stock_values = self._get_indicator(indicator, i_params)
            if stock_values is None:
                raise ValueError(f'Indicator {indicator} with params {i_params} not found.')
            self._indicators[indicator] = np.stack([values for values in stock_values.values()], axis=1)
        
        self._iterate_indicators = {stock: {indicator: None for indicator in params} for stock in self._stocks}  
        self._indexes = product(range(len(self._stocks)), self._indicators)
        self._L = len(self._indicators[list(self._indicators.keys())[0]])

    def __len__(self):
        return self._L

    def iterate_indicators(self, params=None):

        # if not self._default:
        #     raise ValueError(f'No default parameters found.')

        params = self._curr_indicator if params is None else self._fill_in_defaults(params)
        

        self._indicators_iterations = {indicator: np.array(list(self._get_indicator(indicator, i_params).values())) for indicator, i_params in params.items()}

        # print(self._indicators_iterations)
        # assert False

        self._iterate_indicators = {stock: {indicator: None for indicator in params} for stock in self._stocks}  

        self._indexes = list(product(range(len(self._stocks)), self._indicators_iterations))
        self._i = 0

        return self
    
    def __iter__(self):
        return self

    def __next__(self):

        # print(self._i, len(self))
        if self._i >= len(self):
            raise StopIteration(f'Index {self._i } out of range.')

        for s, indicator in self._indexes: 
            self._iterate_indicators[self._stocks[s]][indicator] = self._indicators_iterations[indicator][s, :self._i]
            # if indicator == 'vol_difference' and self._i == 5:
            #     print(self._indicators_iterations['vol_difference'])
            #     print('--------------------------')
            #     print(self._indicators_iterations['vol_difference'][s, :self._i+1])
            #     assert False
        self._i += 1
        
        return self._iterate_indicators
