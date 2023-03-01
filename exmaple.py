# this is for development
from qfinuwa import Strategy
from qfinuwa import Backtester
from qfinuwa import API

import random

class RandomStrategy(Strategy):

        @Strategy.indicator
        def vol_difference(data, lookback=100, gum = None):
            return data['volume'].diff() + lookback

        @Strategy.indicator
        def cumsum(data, sum=None):
            return data['volume'].cumsum()

        def __init__(self, name=None, bruh=None):
            super().__init__()
            self.dir = ['BUY', 'SELL']


        def on_data(self, data, indicators, portfolio):

            for stock in portfolio.stocks:
                for _ in data: pass
                for _ in indicators: pass
                action = [portfolio.enter_long, portfolio.sell_long, portfolio.enter_short, portfolio.cover_short][random.randint(0,3)]
                action(stock, 1)

            return


if __name__ == "__main__":

    data_folder_dir = r"C:\Users\isaac\Downloads\data"

    data_fetcher = API(api_key_path='API_key.txt',
                    data_folder=data_folder_dir)

    # data_fetcher.fetch_data(['GOOG', 'AAPL', 'TSLA', 'IBM'])

    backtester = Backtester( ['AAPL', 'GOOG'],
                            data=data_folder_dir,  months=3, fee=0.01)

    backtester.update_strategy(RandomStrategy)


    backtester.set_strategy_params({
        "name": "Test",
    })

    backtester.set_indicator_params({
        "vol_difference": {
            "lookback": 50,
            "gum": "a",
        },
        "cumsum": {
            "sum": -2,
    }})

    results = backtester.run()

    r = results[0]


    # import time

    # s = time.time()
    # a_params, i_params = {"name": ['Test'], "bruh": [1,2 ]}, {"vol_difference": {"lookback": [0, 1], "gum": ['a', 'c']}, "cumsum": {"cummie": [-2]}}
    # results = backtester.backtest_strategies(a_params, i_params, multiprocessing=True)
    # print(time.time()-s)
    # results = backtester.run()


