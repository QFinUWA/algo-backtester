import numpy as np
import pandas as pd
from itertools import product


class Portfolio:

    def __init__(self, stocks: list, cash: float, fee: float, ticks: int):

        self._curr_prices = None

        self._i = -1
        self._cash = cash
        # TODO: arg checking
        self._fee_mult = 1 + fee
        self._fee_div = 1 - fee
        self._stocks = stocks
        self._stock_to_id = {stock: i for i, stock in enumerate(stocks)}

        self._short_value = 0
        self._longs = {stock: 0 for stock in stocks}
        # maybe make a heap or linked list??
        self._shorts = {stock: [] for stock in stocks}
        # history is an array of every buy/sell order
        # stock 0's entry is at row indexes (0, 1, 2, 3) for (long_buy, short_buy, long_sell, short_sell)

        pos_types = ['long', 'sell', 'short', 'cover']
        self._history_cols = [
            'balance'] + [f'{stock}_{longs}' for stock, longs in product(self._stocks, pos_types)]
        self._history = np.zeros((ticks, 1 + len(stocks)*4))

    @property
    def curr_prices(self):
        return self._curr_prices

    @curr_prices.setter
    def curr_prices(self, prices):
        self._i += 1
        self._history[self._i, 0] = self._cash
        self._curr_prices = prices

    @property
    def cash(self):
        return self._cash

    @cash.setter
    def cash(self, _):
        raise ValueError('Cannot modify Portfolio.cash ... you cheeky bugger')

    @property
    def history(self):
        df = pd.DataFrame(np.array(self._history), columns=self._history_cols)
        df['balance'] = df['balance'].shift(-1)
        df.iloc[-1,  0] = self._cash
        return df

    def _add_to_history(self,  stock,  sell,  amount):
        j = 1 + self._stock_to_id[stock]*4 + sell
        self._history[self._i, j] += amount

    def enter_long(self,  stock,  quantity):

        cost = quantity*self._curr_prices[stock]*self._fee_mult

        if cost > self._cash:
            return 0

        self._cash -= cost

        self._longs[stock] += quantity
        self._add_to_history(stock, 0, quantity)

        return 1

    def sell_long(self,  stock,  quantity):

        price = quantity*self._curr_prices[stock]*self._fee_div

        self._cash += price

        self._longs[stock] -= quantity
        self._add_to_history(stock, 1, quantity)

        return 1

    def enter_short(self,  stock,  quantity):

        price = quantity*self._curr_prices[stock]*self._fee_mult

        if self._short_value + price > self._cash:
            return 0

        self._short_value += price

        self._shorts[stock].append((price, quantity))

        self._add_to_history(stock, 2, quantity)

        return 1

    def cover_short(self,  stock,  quantity):

        profit = 0
        price = self._curr_prices[stock]
        i = 0
        for cost, quant in self._shorts[stock]:
            if quant > quantity:
                break
            quantity -= quant
            profit += quant*(cost-price)
            self._short_value -= cost
            i += 1

        if i == 0:
            return 0

        self._cash += profit*self._fee_div

        self._shorts[stock] = self._shorts[stock][i:]

        self._add_to_history(stock, 3, quantity)

        return 1
