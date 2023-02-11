# this is for development
from qfin.algorithm import Algorithm
from qfin.backtester import Backtester
from qfin.API import API

import random
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')

class ExampleAlgorithm(Algorithm):

        @Algorithm.indicator
        def vol_difference(data, lookback=100, gum = None):
            return data['volume'].diff() + lookback

        @Algorithm.indicator
        def cumsum(data, cummie=None):
            return data['volume'].cumsum()

        def __init__(self, name=None, bruh=None):
            super().__init__()
            self.dir = ['BUY', 'SELL']


        def on_data(self, data, portfolio):
            prices, indicators = data
            
            # return
            if random.random() > 0.9999:
                self.dir = self.dir[::-1]
                # print('swapped')

            for stock in prices:
                # if self.dir[0] == 'SELL':
                #     if portfolio.enter_short(stock, 2) == 0:
                #         portfolio.cover_short(stock, 2)
                # else:
                if portfolio.enter_long(stock, 2) == 0:
                    portfolio.sell_long(stock, 2)
        
            return


if __name__ == "__main__":
    print(ExampleAlgorithm.defaults())
    data_folder_dir = r"C:\Users\isaac\Downloads\data"

    data_fetcher = API(api_key_path='API_key.txt',
                    data_folder=data_folder_dir)

    # data_fetcher.fetch_data(['GOOG', 'AAPL', 'TSLA', 'IBM'])

    backtester = Backtester( ['AAPL', 'GOOG'],
                            data=data_folder_dir,  months=3, fee=0.01)

    backtester.set_algorithm(ExampleAlgorithm)


    backtester.set_algorithm_params({
        "name": "Test",
    })

    backtester.set_indicator_params({
        "vol_difference": {
            "lookback": 50,
            "gum": "a",
        },
        "cumsum": {
            "cummie": -2,
    }})

    results = backtester.run()

    r = results[0]
    print(r.cash[:20])


    # import time

    # s = time.time()
    # a_params, i_params = {"name": ['Test'], "bruh": [1,2 ]}, {"vol_difference": {"lookback": [0, 1], "gum": ['a', 'c']}, "cumsum": {"cummie": [-2]}}
    # results = backtester.backtest_strategies(a_params, i_params, multiprocessing=True)
    # print(time.time()-s)
    # results = backtester.run()


