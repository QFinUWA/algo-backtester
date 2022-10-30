from qfin import StockData, Algorithm, Backtester

stock_data = StockData(stocks=[
    'apple'], period='2022-2023')


def vol_difference(data):
    return data['volume'].diff()


stock_data.add_indicator('volume_diff', vol_difference)
stock_data.add_indicator('cum_sum', lambda data: data['price'].cumsum())


class ExampleAlgorithm(Algorithm):

    def __init__(self):
        super().__init__()

    # def on_data(self, data):
    #     # accessing indicators
    #     apple_vol_diff = data['apple']['volume_diff']

    #     google_zero_or_one = data['google']['zeroes_ones']

    #     average_cum_sum = data['google'].mean()

    #     # TODO - think of a more clear way to implement
    #     self.buy('apple', 'long', self.cash)
    #     self.sell('apple', 'long', 10)
    #     self.buy('google', 'short', self.cash)


strategy = ExampleAlgorithm()
backtester = Backtester(stock_data, sample_period='3 months',
                        overlap=True, samples=20, fee=0.01)


results = backtester.backtest_strategy(strategy)
