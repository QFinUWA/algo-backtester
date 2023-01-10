import numpy as np
import pandas as pd
from itertools import product
import heapq
from prettytable import PrettyTable


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

        # self._short_value = 0
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

    def __str__(self):
        t = PrettyTable(['Stock', 'Longs', 'Shorts'])
        for stock in self._stocks:
            # print([stock, self._longs[stock], sum(q for _, q in self._shorts[stock])])
            t.add_row([stock, self._longs[stock], sum(q for _, q in self._shorts[stock])])
            
        return f'${self._cash}\n' + str(t)

    def _add_to_history(self,  stock,  sell,  amount):
        j = 1 + self._stock_to_id[stock]*4 + sell
        self._history[self._i, j] += amount

    def enter_long(self,  stock,  quantity=None, cost=None):

        if not bool(quantity) ^ bool(cost):
            raise TypeError('Please input quanity OR cost.')

        ##
        if bool(cost):
            quantity = cost*self._fee_div/self._curr_prices[stock]
        
        ##
        elif bool(quantity):
            cost = quantity*self._curr_prices[stock]*self._fee_mult

        if cost > self._cash:
            return 0

        self._cash -= cost

        self._longs[stock] += quantity
        self._add_to_history(stock, 0, quantity)

        return 1

    def sell_long(self,  stock,  quantity=None, cost=None):

        if not bool(quantity) ^ bool(cost):
            raise TypeError('Please input quanity OR cost.')

        ##
        if bool(cost):
            quantity = cost*self._fee_div/self._curr_prices[stock]

        ##
        elif bool(quantity):
            price = quantity*self._curr_prices[stock]*self._fee_div
            

        self._cash += price

        self._longs[stock] -= quantity
        self._add_to_history(stock, 1, quantity)

        return 1

    def enter_short(self,  stock,  quantity=None, cost=None):

        if not bool(quantity) ^ bool(cost):
            raise TypeError('Please input quanity OR cost.')

        ##
        if bool(cost):
            quantity = cost*self._fee_div/self._curr_prices[stock]

        ##
        elif bool(quantity):
            price = quantity*self._curr_prices[stock]*self._fee_mult
    
        if price > self._cash:

            return 0

        # self._short_value += price
        self._cash -= price

        heapq.heappush(self._shorts[stock], (-price, quantity))

        self._add_to_history(stock, 2, quantity)
        # if self._i > 682500:
        #     print(f'shorted {stock}, {quantity}')
        #     print(self._short_value, price , self._cash)
        return 1

    def cover_short(self,  stock,  quantity):

        quantity = cost*self._fee_div/self._curr_prices[stock]          
        profit = 0
        deposit = 0
        price = self._curr_prices[stock]

        rem_quantity = quantity
        while self._shorts[stock]:
            cost, quant = self._shorts[stock][0]

            cost *= -1
            # no more shorts to sell
            if rem_quantity == 0:
                break

            # cannot sell whole position - sell franction
            if quant > rem_quantity:
                # TODO: if float else int
                frac = rem_quantity/quant
                
                self._shorts[stock][0] = -cost*frac, quant*frac
                rem_quantity = 0
                frac_cost = frac*cost
                deposit += frac_cost
                profit += frac_cost - frac*quantity

                break
            heapq.heappop(self._shorts[stock])

            rem_quantity -= quant
            deposit += cost
            profit += cost - quant*price
            # self._short_value -= cost

        if rem_quantity == quantity:
            return 0
        # if self._i > 682500:
        #     print(f'covered {stock}, {quantity_o} $({profit*self._fee_div})')

        self._cash += deposit + profit*self._fee_div

        self._add_to_history(stock, 3, quantity)

        return 1
