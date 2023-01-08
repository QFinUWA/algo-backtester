# this is for development
from qfin.backtester import Algorithm, Backtester
from qfin.API import API

data_folder_dir = r"C:\Users\isaac\Downloads\data"

data_fetcher = API(api_key_path='API_key.txt',
                   data_folder=data_folder_dir)

# data_fetcher.fetch_data(['GOOG', 'AAPL', 'TSLA', 'IBM'])


class ExampleAlgorithm(Algorithm):

    def __init__(self, name=None):
        super().__init__()
        self.name = name

    @Algorithm.indicator
    def vol_difference(data, lookback=100):

        return data['volume'].diff()

    def on_data(self, data, portfolio):
        for stock in data:
            if portfolio.enter_long(stock, 1) == 0:
                portfolio.sell_long(stock, 1)
        return


backtester = Backtester(ExampleAlgorithm, ['AAPL', 'GOOG'],
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
