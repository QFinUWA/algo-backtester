import unittest

from src.qfinuwa import Indicators
from src.qfinuwa.opt import StockData

class TestStringMethods(unittest.TestCase):

    def setUp(self) -> None:
        # self.stock_data = StockData(['AAPL'], 'data', verbose=False)
        self.stock_data = {'AAPL': [1,2,3], 'GOOG': [4,5,6]}


    def test_empty_setup(self):

        indicators = Indicators(self.stock_data)

        self.assertDictEqual(indicators.params, dict())
        self.assertDictEqual(indicators._funcn_to_indicator_map, dict())
        self.assertListEqual(indicators.indicators, [])
        self.assertListEqual(indicators.indicator_groups, [])
        self.assertDictEqual(indicators._indicator_functions, dict())
        self.assertDictEqual(indicators.defaults, dict())
    
    def test_extended_setup(self):

        class ExtendedIndicators(Indicators):

            @Indicators.Indicator
            def a(self, data):
                return {'a1': [2*d for d in data]}

            def helper_b1(self, data):
                return [-d for d in data]

            @Indicators.Indicator
            def b(self, data, bp1 = 1, bp2 = 2):
                return {'b2': data, 'b1': self.helper_b1(data)}


        indicators = ExtendedIndicators(self.stock_data)

        funcn_to_indicator_map_expected = {
            'a': ['a1'], 
            'b': ['b1', 'b2']
        }
        self.maxDiff = None
        self.assertDictEqual(indicators.params, {'a': {}, 'b': {'bp1': 1, 'bp2': 2}})
        self.assertDictEqual(indicators._funcn_to_indicator_map, funcn_to_indicator_map_expected)
        self.assertListEqual(indicators.indicators, ['a1', 'b1', 'b2'])
        self.assertListEqual(indicators.indicator_groups, ['a', 'b'])
        self.assertSetEqual(set(indicators._indicator_functions.keys()), {'a', 'b'})
        for f, func in indicators._indicator_functions.items():
            self.assertTrue(callable(func))
            self.assertTrue(hasattr(func, 'Indicator'))
        self.assertDictEqual(indicators.defaults, {'a': {}, 'b': {'bp1': 1, 'bp2': 2}})
        self.assertDictEqual(indicators._cache, 
                            {('a', ()): {'a1': {'AAPL': [2, 4, 6], 'GOOG': [8, 10, 12]}}, ('b', (('bp1', 1), ('bp2', 2))): {'b1': {'AAPL': [-1, -2, -3], 'GOOG': [-4, -5, -6]}, 'b2': {'AAPL': [1, 2, 3], 'GOOG': [4, 5, 6]}}})

    def test_cache(self):

        class ExtendedIndicators(Indicators):

            @Indicators.Indicator
            def b(self, data, bp1 = 1, bp2 = 2):
                return {'b2': [bp2+d for d in data], 'b1': [bp1+d for d in data]}
        
        indicators = ExtendedIndicators(self.stock_data)

        self.assertDictEqual(indicators._cache, {('b', (('bp1', 1), ('bp2', 2))): {'b1': {'AAPL': [2, 3, 4], 'GOOG': [5, 6, 7]}, 'b2': {'AAPL': [3, 4, 5], 'GOOG': [6, 7, 8]}}})

        indicators.add_parameters({'b': {'bp1': 0, 'bp2': 0}})

        self.assertDictEqual(indicators._cache, {('b', (('bp1', 1), ('bp2', 2))): {'b1': {'AAPL': [2, 3, 4], 'GOOG': [5, 6, 7]}, 'b2': {'AAPL': [3, 4, 5], 'GOOG': [6, 7, 8]}}, ('b', (('bp1', 0), ('bp2', 0))): {'b1': {'AAPL': [1, 2, 3], 'GOOG': [4, 5, 6]}, 'b2': {'AAPL': [1, 2, 3], 'GOOG': [4, 5, 6]}}})

        self.assertTrue(indicators._is_cached('b', {'bp1': 0, 'bp2': 0}))

    def test_update_params(self):

        class ExtendedIndicators(Indicators):

            @Indicators.Indicator
            def a(self, data, ap1 = 1):
                return {'a1': [ap1 for d in data]}

            @Indicators.Indicator
            def b(self, data, bp1 = 1, bp2 = 2):
                return {'b2': [bp2+d for d in data], 'b1': [bp1+d for d in data]}

        indicators = ExtendedIndicators(self.stock_data)

        indicators.update_parameters({'b': {'bp1': 0, 'bp2': 0}, 'a': {'ap1': 0}})

        # check cache updated
        self.assertDictEqual(indicators._cache, {('b', (('bp1', 1), ('bp2', 2))): {'b1': {'AAPL': [2, 3, 4], 'GOOG': [5, 6, 7]}, 'b2': {'AAPL': [3, 4, 5], 'GOOG': [6, 7, 8]}}, ('b', (('bp1', 0), ('bp2', 0))): {'b1': {'AAPL': [1, 2, 3], 'GOOG': [4, 5, 6]}, 'b2': {'AAPL': [1, 2, 3], 'GOOG': [4, 5, 6]}}, ('a', (('ap1', 0),)): {'a1': {'AAPL': [0, 0, 0], 'GOOG': [0, 0, 0]}}, ('a', (('ap1', 1),)): {'a1': {'AAPL': [1, 1, 1], 'GOOG': [1, 1, 1]}}})
        # check params updated
        self.assertDictEqual(indicators.params, {'b': {'bp1': 0, 'bp2': 0}, 'a': {'ap1': 0}})


                # check cache updated
        indicators.update_parameters({'b': {'bp1': -1}})

        self.assertDictEqual(indicators._cache, {('b', (('bp1', 1), ('bp2', 2))): {'b1': {'AAPL': [2, 3, 4], 'GOOG': [5, 6, 7]}, 'b2': {'AAPL': [3, 4, 5], 'GOOG': [6, 7, 8]}}, ('b', (('bp1', 0), ('bp2', 0))): {'b1': {'AAPL': [1, 2, 3], 'GOOG': [4, 5, 6]}, 'b2': {'AAPL': [1, 2, 3], 'GOOG': [4, 5, 6]}}, ('a', (('ap1', 0),)): {'a1': {'AAPL': [0, 0, 0], 'GOOG': [0, 0, 0]}}, ('a', (('ap1', 1),)): {'a1': {'AAPL': [1, 1, 1], 'GOOG': [1, 1, 1]}}, ('b', (('bp1', -1), ('bp2', 0))): {'b1': {'AAPL': [0, 1, 2], 'GOOG': [3, 4, 5]}, 'b2': {'AAPL': [1, 2, 3], 'GOOG': [4, 5, 6]}}})

        # check params updated
        self.assertDictEqual(indicators.params, {'b': {'bp1': -1, 'bp2': 0}, 'a': {'ap1': 0}})

        indicators.update_parameters({})

        self.assertDictEqual(indicators.params, {'b': {'bp1': -1, 'bp2': 0}, 'a': {'ap1': 0}})

        self.assertRaises(ValueError, indicators.update_parameters, {'b': {'bp1': 0, 'bp2': 0}, 'a': {'ap1': 0}, 'c': {'cp1': 0}})
        self.assertRaises(ValueError, indicators.update_parameters, {'b': {'bp1': 0, 'bp2': 0}, 'a': {'bp1': 0}})

    def test_permutations(self):
        
        class ExtendedIndicators(Indicators):

            @Indicators.Indicator
            def a(self, data, ap1 = 0):
                return {'a1': [ap1*d for d in data]}

            def helper_b1(self, data):
                return [-d for d in data]

            @Indicators.Indicator
            def b(self, data, bp1 = 1, bp2 = 2):
                return {'b2': data, 'b1': self.helper_b1(data)}

        indicators = ExtendedIndicators(self.stock_data)
        self.assertDictEqual(indicators._fill_in_params({'a': {'ap1': 0}, 'b': {'bp1': 0, 'bp2': 2}}), {'a': {'ap1': 0}, 'b': {'bp1': 0, 'bp2': 2}})
        self.assertDictEqual(indicators._fill_in_params({'a': {'ap1': 1}, 'b': {'bp1': 1, 'bp2': 3}}), {'a': {'ap1': 1}, 'b': {'bp1': 1, 'bp2': 3}})

        # res = indicators.get_permutations({'a': {'ap1': [0, 1, -1] }, 'b': {'bp1': [0,1], 'bp2': [2,3]}})

        # print(res)

        # self.assertListEqual(res, [
        # {'a': {'ap1': 0}, 'b': {'bp1': 0, 'bp2': 2}}, 
        # {'a': {'ap1': 0}, 'b': {'bp1': 0, 'bp2': 3}}, 
        # {'a': {'ap1': 0}, 'b': {'bp1': 1, 'bp2': 2}}, 
        # {'a': {'ap1': 0}, 'b': {'bp1': 1, 'bp2': 3}}, 
        # {'a': {'ap1': 1}, 'b': {'bp1': 0, 'bp2': 2}}, 
        # {'a': {'ap1': 1}, 'b': {'bp1': 0, 'bp2': 3}}, 
        # {'a': {'ap1': 1}, 'b': {'bp1': 1, 'bp2': 2}}, 
        # {'a': {'ap1': 1}, 'b': {'bp1': 1, 'bp2': 3}}, 
        # {'a': {'ap1': -1}, 'b': {'bp1': 0, 'bp2': 2}}, 
        # {'a': {'ap1': -1}, 'b': {'bp1': 0, 'bp2': 3}}, 
        # {'a': {'ap1': -1}, 'b': {'bp1': 1, 'bp2': 2}}, 
        # {'a': {'ap1': -1}, 'b': {'bp1': 1, 'bp2': 3}}])

        # [
        # {'a': {'ap1': -1}, 'b': {'bp1': 1, 'bp2': 3}}, 
        # {'a': {'ap1': -1}, 'b': {'bp1': 1, 'bp2': 3}}, 
        # {'a': {'ap1': -1}, 'b': {'bp1': 1, 'bp2': 3}}, 
        # {'a': {'ap1': -1}, 'b': {'bp1': 1, 'bp2': 3}}, 
        # {'a': {'ap1': -1}, 'b': {'bp1': 1, 'bp2': 3}}, 
        # {'a': {'ap1': -1}, 'b': {'bp1': 1, 'bp2': 3}}, 
        # {'a': {'ap1': -1}, 'b': {'bp1': 1, 'bp2': 3}}, 
        # {'a': {'ap1': -1}, 'b': {'bp1': 1, 'bp2': 3}}, 
        # {'a': {'ap1': -1}, 'b': {'bp1': 1, 'bp2': 3}}, 
        # {'a': {'ap1': -1}, 'b': {'bp1': 1, 'bp2': 3}}, 
        # {'a': {'ap1': -1}, 'b': {'bp1': 1, 'bp2': 3}}, 
        # {'a': {'ap1': -1}, 'b': {'bp1': 1, 'bp2': 3}}]

        res = indicators.get_permutations({})
        self.assertListEqual(res, [indicators.params])

    # def test_iterate(self):
        
    #     class ExtendedIndicators(Indicators):

    #         @Indicators.Indicator
    #         def a(self, data, ap1 = 0):
    #             return {'a1': [ap1 for d in data]}

    #         @Indicators.Indicator
    #         def b(self, data, bp1 = 0, bp2 = 0):
    #             return {'b2': [bp2+d for d in data], 'b1': [bp1+d for d in data]}
        
    #     indicators = ExtendedIndicators(self.stock_data)

    #     it = indicators.iterate_params()

    #     self.assertDictEqual(next(it), {'AAPL': {'a1': [0], 'b1': [1], 'b2': [1]}, 'GOOG': {'a1': [0], 'b1': [4], 'b2': [4]}})
    #     self.assertDictEqual(next(it), {'AAPL': {'a1': [0,0], 'b1': [1,2], 'b2': [1,2]}, 'GOOG': {'a1': [0,0], 'b1': [4,5], 'b2': [4,5]}})
    #     self.assertDictEqual(next(it), {'AAPL': {'a1': [0,0,0], 'b1': [1,2,3], 'b2': [1,2,3]}, 'GOOG': {'a1': [0,0,0], 'b1': [4,5,6], 'b2': [4,5,6]}})

        
    #     it = indicators.iterate_params()

    #     self.assertDictEqual(next(it), {'AAPL': {'a1': [0], 'b1': [1], 'b2': [1]}, 'GOOG': {'a1': [0], 'b1': [4], 'b2': [4]}})
    #     self.assertDictEqual(next(it), {'AAPL': {'a1': [0,0], 'b1': [1,2], 'b2': [1,2]}, 'GOOG': {'a1': [0,0], 'b1': [4,5], 'b2': [4,5]}})
    #     self.assertDictEqual(next(it), {'AAPL': {'a1': [0,0,0], 'b1': [1,2,3], 'b2': [1,2,3]}, 'GOOG': {'a1': [0,0,0], 'b1': [4,5,6], 'b2': [4,5,6]}})

    #     it = indicators.iterate_params({'a': {'ap1': 10 }, 'b': {'bp1': 10, 'bp2': 10}})

    #     self.assertDictEqual(next(it), {'AAPL': {'a1': [10], 'b1': [11], 'b2': [11]}, 'GOOG': {'a1': [10], 'b1': [14], 'b2': [14]}})
    #     self.assertDictEqual(next(it), {'AAPL': {'a1': [10,10], 'b1': [11,12], 'b2': [11,12]}, 'GOOG': {'a1': [10,10], 'b1': [14,15], 'b2': [14,15]}})
    #     self.assertDictEqual(next(it), {'AAPL': {'a1': [10,10,10], 'b1': [11,12,13], 'b2': [11,12,13]}, 'GOOG': {'a1': [10,10,10], 'b1': [14,15,16], 'b2': [14,15,16]}})

        it = indicators.iterate_params({'a': {'ap1': -1 }}) # TODO:
if __name__ == '__main__':
    unittest.main()