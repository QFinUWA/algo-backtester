


# this is for development
from src.qfinuwa import API, Backtester, Algorithm

import random



data_folder_dir = r"C:\Users\isaac\Downloads\data"

data_fetcher = API(api_key_path='API_key.txt',
                data_folder=data_folder_dir)


class ExampleAlgorithm(Algorithm):

    @Algorithm.indicator
    def vol_difference(data, lookback=50, gum = None):
        return data['volume'].diff() + lookback

    @Algorithm.indicator
    def cumsum(data, cummie=None):
        return data['volume'].cumsum()

    def __init__(self, name=None, bruh=None):
        super().__init__()
        self.dir = ['BUY', 'SELL']


    def on_data(self, prices, indicators, portfolio):
        
        # return
        if random.random() > 0.999:
            self.dir = self.dir[::-1]
            # print('swapped')

        for stock in prices:
            # if self.dir[0] == 'SELL':
            #     if portfolio.enter_short(stock, 2) == 0:
            #         portfolio.cover_short(stock, 2)
            # else:
            if portfolio.enter_short(stock, 2) == 0:
                # portfolio.sell_long(stock, 2)
                pass
    
        return


# data_fetcher.fetch_data(['GOOG', 'AAPL', 'TSLA', 'IBM'])
backtester = Backtester(['AAPL'], data=data_folder_dir, strategy=ExampleAlgorithm, days=100, fee=0.01)

backtester.update_algorithm(ExampleAlgorithm)
backtester._strategy.defaults()['indicators']
backtester.indicator_params

backtester.set_algorithm_params({
    'bruh': "test",
})

backtester.set_indicator_params({
    "vol_difference": {
        "lookback": 20,
        "gum": "a",
    },
    "cumsum": {
        "cummie": -1,
}})



s = {'bruh': 'a'}
i = {'vol_difference': {
    'lookback': [20, 30]
}}

results = backtester.backtest_strategies(s, i, cv=2)