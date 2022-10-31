from qfin import Algorithm, Backtester

backtester = Backtester(stocks=['apple'], period='2022-2023', sample_period='3 months',
                        overlap=True, samples=20, fee=0.01)


class ExampleAlgorithm(Algorithm):

    def __init__(self):
        super().__init__()

        self.add_indicator('volume_diff', self.vol_difference)
        self.add_indicator('cum_sum', lambda data: data['price'].cumsum())

    def vol_difference(self, data):
        return data['volume'].diff()


strategy = ExampleAlgorithm()

backtester.update_indicators(only=['volume_diff'])

results = backtester.backtest_strategy(strategy, )
