import pandas as pd
import numpy as np
from tqdm import tqdm
from .stockdata import StockData
from .algorithm import Algorithm


class Backtester:

    def __init__(self, stocks=['apple'], period='2022-2023', frequency='1T', sample_period='3 months', overlap=True, samples=20, fee=0.005):

        self._data = StockData(
            stocks=stocks, period=period, frequency=frequency)
        self._fee = fee
        self._stocks = stocks

        self._update_indicators = None

    @property
    def fee(self):
        return self._fee

    @property
    def stocks(self):
        return self._data.stocks

    def update_indicators(self, only: list = None):

        if not self._update_indicators:
            self._update_indicators = list()

        for indicator in (only or self._data.indicators[2:]):

            if indicator not in self._update_indicators:
                self._update_indicators.append(indicator)

    def backtest_strategy(self, strategy: Algorithm):
        if self._update_indicators is None:
            self.update_indicators()

        self._data.add_indicators(
            {k: v for k, v in strategy.indicator_functions.items() if k in self._update_indicators})

        self._update_indicators = None

        for t in tqdm(iter(self._data)):
            strategy.on_data(t)
