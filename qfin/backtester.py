import pandas as pd
import numpy as np
from tqdm import tqdm
from .stockdata import StockData
from .algorithm import Algorithm


class Backtester:

    def __init__(self, stock_data: StockData, sample_period='3 months', overlap=True, samples=20, fee=0.005):

        self._data = stock_data
        self._data.compress_data()
        self._fee = fee

    @property
    def fee(self):
        return self._fee

    @property
    def stocks(self):
        return self._data.stocks

    def backtest_strategy(self, strategy: Algorithm):

        strategy.assimilate_backtester(self.fee, self.stocks)
        for t in tqdm(iter(self._data)):
            strategy.on_data(t)

    # TODO

    def backtest_strategies(self, algorithm: Algorithm, parameters: dict):
        pass
