import numpy as np
import pandas as pd

class Portfolio:

    def __init__(self, stocks: list, cash: float, fee: float, ticks: int):

        self._curr_prices = None

        self._i = -1
        self._cash = cash
        self._fee = fee
        self._stocks = stocks

        self._stock_id = {stock: i for i, stock in enumerate(stocks)}

        self._curr_longs = {stock: 0 for stock in stocks}
        self._curr_shorts = {stock: 0 for stock in stocks}

        # history is an array of every buy/sell order
        # stock 0's entry is at row indexes (0, 1, 2, 3) for (long_buy, short_buy, long_sell, short_sell)
        self._history = np.zeros((ticks, len(stocks)*4))

    @property
    def curr_prices(self):
        return self._curr_prices

    @curr_prices.setter
    def curr_prices(self, prices):
        self._i += 1
        self._curr_prices = prices

    def get_longs(self, stock):

        if stock not in self._curr_longs:
            raise ValueError(f'Stock does not exist.')

        self._curr_longs[stock]

    def get_shorts(self, stock):

        if stock not in self._curr_shorts:
            raise ValueError(f'Stock does not exist.')

        self._curr_shorts[stock]

    def _check_long_short(self, string):
        if string not in ['short', 'long']:
            raise ValueError(
                f'parameter long must be either \'long\' or \'short\'')

    def enter_position(self, long, stock, quantity=None, value=None):

        self._check_long_short(long)

        if not (bool(quantity) ^ bool(value)):
            raise ValueError(
                f'Please set one quantity or value using quanitity= or value=.')

        # print(self._curr_prices)
        if quantity:
            quantity = (
                quantity * self._curr_prices[stock] * (1 - self._fee))/self._curr_prices[stock]

        else:
            quantity = price*(1-self._fee)/self._prices[stock]

        # TODO: check cash isn't negative
        self._cash -= 0

        self._history[self._i, 4*(len(self._stocks)-1) +
                      int(long == 'short')] += 1

        return True

    def exit_position(self, long, stock, quantity=None, value=None):

        self._check_long_short(long)

        if not (bool(quantity) ^ bool(value)):
            raise ValueError(
                f'Please set one quantity or value using quanitity= or value=.')

        if quantity:
            quantity = (
                quantity * self._curr_prices[stock] * (1 - self._fee))/self._curr_prices[stock]

        else:
            quantity = price*(1-self._fee)/self._prices[stock]

        self._cash += price

        self._history[self._i, 4 *
                      len(self._stocks) + int(long == 'short') + 2] += 1

        return True
