# this is for development
from qfin.algorithm import Algorithm
from qfin.backtester import Backtester
from qfin.API import API

data_folder_dir = r"C:\Users\isaac\Downloads\data"

data_fetcher = API(api_key_path='API_key.txt',
                   data_folder=data_folder_dir)

# data_fetcher.fetch_data(['GOOG', 'AAPL', 'TSLA', 'IBM'])


class ExampleAlgorithm(Algorithm):

    def __init__(self, name=None):
        super().__init__()
        self.i = 0
        self.dir = ['BUY', 'SELL']

    @Algorithm.indicator
    def vol_difference(data, lookback=100):
        return data['volume'].diff()

    def on_data(self, data, portfolio):
        if self.i > 100000:
            self.dir = self.dir[::-1]
        # return
        for stock in data:
            if portfolio.enter_long(stock, 2) == 0:
                # portfolio.cover_short(stock, 2)
                # print(f'COVER {stock}')
                continue

            # trade = portfolio.en
            # print(f'SHORT {stock}')
        
        # self.i += 1
        # if self.i == 25:
        #     assert False
        return


backtester = Backtester(ExampleAlgorithm, ['AAPL'],
                        data=data_folder_dir,  tests=20)

backtester.set_algorithm_params({
    "name": "Test",
})

backtester.set_indicator_params({
    "vol_difference": {
        "lookback": 1,
    }
})

results = backtester.run()

results.to_csv('results.csv')