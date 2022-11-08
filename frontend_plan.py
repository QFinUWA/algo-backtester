from qfin.backtester import Algorithm, Backtester

backtester = Backtester(stocks=['apple', 'google', 'downwards', 'upwards'], period='2022-2023', sample_period='3 months',
                        overlap=True, samples=20)


class ExampleAlgorithm(Algorithm):

    def __init__(self):
        super().__init__()

        self.add_indicator('volume_diff', self.vol_difference)
        self.add_indicator('cum_sum', lambda data: data['price'].cumsum())

    def vol_difference(self, data):
        return data['volume'].diff()

    def on_data(self, data: dict, portfolio):

        for _ in range(100):
            portfolio.buy('google', 1, 0)
            print(portfolio.cash)
        assert 1 == 0
        # if 10 < 2:
        #     for i in range(100):
        #         1 + 2

        # for _ in range(5):
        #     portfolio.enter_position('long', 'apple', 10, 0)
        pass


strategy = ExampleAlgorithm()

backtester.update_indicators(only=['volume_diff'])

results = backtester.backtest_strategy(strategy, cash=10000, fee=0.005)

print(results)

# results = backtester.backtest_straties(ExampleAlgorithm, {
#                                        'test': ['multi'], 'test2': ['multi2a', 'multi2b']}, cash=69, fee=0.005)
