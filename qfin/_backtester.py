import pandas as pd
import numpy as np
from tqdm import tqdm
from .stockdata import StockData


class Backtester:

    def __init__(self, fee=0.005, frequency='15mins', stocks=['apple', 'google'], period='2022-2023'):

        self._stock_data = StockData(stocks)

    @property
    def stocks(self):
        return self._stock_data.stocks

    @property
    def df(self):
        return self._init_data

    @property
    def price(self):
        return {stock: self._init_data[stock]['price'] for stock in self._stocks}

    @property
    def volume(self):
        return {stock: self._init_data[stock]['volume'] for stock in self._stocks}

    def add_indicator(self, name, func):
        self._stock_data.add_indicator(name, func)

    def add_indicators(self, table):
        self._stock_data.add_indicators(table)

    def _backtest(self, algorithm, fee=0, sample_period='3m', overlap=False, samples=1, multiprocessing=True):
        pass
        # strategy = algorithm()
        # strategy.load_stocks(self.stocks)
        # strategy.add_fee(fee)

        # for i in tqdm(range(len(self._init_data['apple']))):
        #     # strategy.on_data(
        #     #     {stock: self._init_data[stock][:i+1] for stock in self._stocks})
        #     strategy.on_data(
        #         (self._init_data['apple'][:i+1],
        #          self._init_data['google'][:i+1]))
