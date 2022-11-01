from qfin import Algorithm, Backtester

backtester = Backtester(stocks=['apple'], period='2022-2023', sample_period='3 months',
                        overlap=True, samples=20)


class ExampleAlgorithm(Algorithm):

    def __init__(self):
        super().__init__()

        self.add_indicator('volume_diff', self.vol_difference)
        self.add_indicator('cum_sum', lambda data: data['price'].cumsum())

    def vol_difference(self, data):
        return data['volume'].diff()

    def on_data(self, data: dict, portfolio: Portfolio):
        # TODO: Make go faster
        for _ in range(100):
            portfolio.enter_position('long', 'apple', quantity=10)


strategy = ExampleAlgorithm()

backtester.update_indicators(only=['volume_diff'])

results = backtester.backtest_strategy(strategy, cash=2000, fee=0.005)

# results = backtester.backtest_straties(ExampleAlgorithm, {
#                                        'test': ['multi'], 'test2': ['multi2a', 'multi2b']}, cash=69, fee=0.005)
