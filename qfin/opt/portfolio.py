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
        self._longs = {stock: [] for stock in stocks}
        # maybe make a heap or linked list??
        self._shorts = {stock: [] for stock in stocks}
        # history is an array of every buy/sell order
        # stock 0's entry is at row indexes (0, 1, 2, 3) for (long_buy, short_buy, long_sell, short_sell)


        # fees = (int)
        # enter_long (time, stock, cost, quantity)
        # exit_long (time, stock, profit, quantity)
        # enter_short (time, stock, cost, quantity)
        # exit_short (time, stock, profit, quantity)

        # pos_types = ['long', 'sell', 'short', 'cover']

        self._cash_history = []

        # self._history_cols = [
        #     'balance'] + [f'{stock}_{longs}' for stock, longs in product(self._stocks, pos_types)]
        # self._history = np.zeros((ticks, 1 + len(stocks)*4))

        self.long_stats = []
        self.short_stats = []       



    @property
    def stocks(self):
        return self._stocks
        
    @property
    def curr_prices(self):
        return self._curr_prices

    @curr_prices.setter
    def curr_prices(self, prices):
        self._i += 1
        self._curr_prices = prices
        self._cash_history.append(self._cash)

    @property
    def cash(self):
        return self._cash

    @cash.setter
    def cash(self, _):
        raise ValueError('Cannot modify Portfolio.cash ... you cheeky bugger')

    # @property
    # def history(self):
    #     df = pd.DataFrame(np.array(self._history), columns=self._history_cols)
    #     df['balance'] = df['balance'].shift(-1)
    #     df.iloc[-1,  0] = self._cash
    #     return df

    @property
    def history(self):
        return (self._cash_history, self.long_stats, self.short_stats)


    def __str__(self):
        t = PrettyTable(['Stock', 'Longs', 'Shorts'])
        for stock in self._stocks:
            # print([stock, self._longs[stock], sum(q for _, q in self._shorts[stock])])
            t.add_row([stock, self._longs[stock], sum(q for _, q in self._shorts[stock])])
            
        return f'${self._cash}\n' + str(t)

    # def _add_to_history(self,  stock,  sell,  amount):
    #     j = 1 + self._stock_to_id[stock]*4 + sell
    #     self._history[self._i, j] += amount

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

        # self._longs[stock] += quantity
        heapq.heappush(self._longs[stock], (cost, quantity))
        # self.hist.append((self._i, 'buy', stock, cost, quantity))

        return 1

    def sell_long(self,  stock,  quantity=None, price=None):

        if not bool(quantity) ^ bool(price):
            raise TypeError('Please input quanity OR cost.')

        ##
        if bool(price):
            quantity = price*self._fee_div/self._curr_prices[stock]

        ##
        elif bool(quantity):
            price = quantity*self._curr_prices[stock]*self._fee_div

        ## --------
        abs_rem = abs_rem_original = quantity if bool(quantity) else price
        total_pay, total_cost = 0, 0

        # print(stock, quantity, price, self._longs)

        while self._longs[stock]:
            # no more shorts to sell
            if abs_rem == 0:
                break

            cos, quant = self._longs[stock][0]

            # quantity we are decreasing to 0 - if quantity is specified 
            # we want to keep closing positions until rem_quanity is 0,
            # same for cost - this is a more consice and neater way to 
            # do this but could also use an if else pattern with repitition 
            abs_amount = quant if bool(quantity) else cos

            # cannot sell whole position - sell franction
            if abs_amount > abs_rem:
                frac = abs_rem/abs_amount
                
                self._longs[stock][0] = cos*(frac-1), quant*(1-frac)
                total_cost += frac*cos
                total_pay += frac*quant*self._curr_prices[stock]
                abs_rem = 0
                break

            heapq.heappop(self._longs[stock])

            abs_rem -= abs_amount
            total_cost += cos
            total_pay += quant*self._curr_prices[stock]
            
        if abs_rem == abs_rem_original:
            # assert False
            return 0
        ## -----
        
        self._cash += total_pay
        # print(total_pay, total_cost)
        self.long_stats.append((self._i, stock, total_pay - total_cost))
        
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

        # self.hist.append((self._i, 'short', stock, price, quantity))

        return 1

    def cover_short(self, stock, quantity=None, cost=None):

        bool_quantity, bool_cost = bool(quantity), bool(cost)

        if not bool_quantity ^ bool_cost:
            raise TypeError('Please input quanity OR cost.')
  
        cost_to_buy = 0
        deposit = 0
        # price = self._curr_prices[stock]
        
        abs_rem = abs_rem_original = quantity if bool_quantity else cost
        while self._shorts[stock]:
            # no more shorts to sell
            if abs_rem == 0:
                break

            cos, quant = self._shorts[stock][0]

            cos *= -1

            # quantity we are decreasing to 0 - if quantity is specified 
            # we want to keep closing positions until rem_quanity is 0,
            # same for cost - this is a more consice and neater way to 
            # do this but could also use an if else pattern with repitition 
            abs_amount = quant if bool_quantity else cos

            # cannot sell whole position - sell franction
            if abs_amount > abs_rem:
                frac = abs_rem/abs_amount
                
                self._shorts[stock][0] = cos*(frac-1), quant*(1-frac)

                deposit += frac*cos
                cost_to_buy += frac*quant*self._curr_prices[stock]
                abs_rem = 0
                break

            heapq.heappop(self._shorts[stock])

            abs_rem -= abs_amount
            deposit += cos
            cost_to_buy += quant*self._curr_prices[stock]

        if abs_rem == abs_rem_original:
            return 0

        profit = deposit - self._fee_mult*cost_to_buy 
        self._cash += profit + deposit

        self.short_stats.append((self._i, stock, profit))
        return 1
