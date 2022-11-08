import numpy as np
import pandas as pd

cdef class Portfolio:

    def __init__(Portfolio self, stocks: list, cash: float, fee: float, ticks: int):

        self._curr_prices = None

        self._i = -1
        self._cash = cash
        # TODO: arg checking
        self._fee_mult = 1 - fee
        self._stocks = stocks
        self._stock_to_id = {stock: i for i, stock in enumerate(stocks)}

        self._stock_id = {stock: i for i, stock in enumerate(stocks)}

        self._curr_longs = {stock: 0 for stock in stocks}
        self._curr_shorts = {stock: 0 for stock in stocks}

        # history is an array of every buy/sell order
        # stock 0's entry is at row indexes (0, 1, 2, 3) for (long_buy, short_buy, long_sell, short_sell)
        self._history = np.zeros((ticks, len(stocks)*2))

    @property
    def curr_prices(self):
        return self._curr_prices

    @curr_prices.setter
    def curr_prices(self, prices):
        self._i += 1
        self._curr_prices = prices

    @property
    def cash(self):
        return self._cash

    @cash.setter
    def cash(self, _):
        raise ValueError('Cannot modify Portfolio.cash ... you cheeky bugger')

    @property
    def history(self):
        return pd.DataFrame(np.array(self._history), columns = np.concatenate([[f'{stock}_buys', f'{stock}_sells'] for stock in self._stocks]))

        
    cpdef _add_to_history(Portfolio self, str stock, int sell, float amount):
        self._history[self._i, self._stock_to_id[stock]*2 + sell] += amount

    def get_longs(self, stock):

        if stock not in self._curr_longs:
            raise ValueError(f'Stock does not exist.')

        self._curr_longs[stock]

    def get_shorts(self, stock):

        if stock not in self._curr_shorts:
            raise ValueError(f'Stock does not exist.')

        self._curr_shorts[stock]


    cpdef public buy(Portfolio self, str stock, float quantity, float value):

        # TODO: Value

        cdef float price = quantity* self._fee_mult*self._curr_prices[stock]        
        if self._cash < price:
            return False
        print('\t', price)
        self._cash -= price

        self._add_to_history(stock, 0, 1)
        return True

    cpdef public sell(Portfolio self, str stock, float quantity, float value):


        if stock not in self._stocks:
            raise ValueError(
                f'{stock} not in list of stocks.'
            )

        cdef float real_quantity = (quantity * self._curr_prices[stock] * self._fee_mult)/self._curr_prices[stock]

        # TODO: Value
        
        # check we have quantity to sell
        # cdef dict positions = self._curr_longs if _long=='long' else self._curr_shorts
        #if positions[stock] < real_quantity:
        #    return False

        self._cash += real_quantity*self._prices[stock]  

        self._add_to_history(stock, 1, 1)

        return True

    cpdef public buy_all(Portfolio self, str stock):
        
        if stock not in self._stocks:
            raise ValueError(
                f'{stock} not in list of stocks.'
            )

        cdef float nshorts = min((self._cash * self._fee_mult)/self._curr_prices[stock], self._curr_shorts[stock])

        self._curr_shorts[stock] -= nshorts

        self._cash -= nshorts * self._curr_prices[stock]

        self._add_to_history(stock, 0, nshorts)

        return False

    cpdef public sell_all(Portfolio self, str stock):
        
        if stock not in self._stocks:
            raise ValueError(
                f'{stock} not in list of stocks.'
            )

        cdef float nlongs = self._curr_longs[stock]
        self._curr_longs[stock] = 0
        self._cash += nlongs * self._prices[stock] * self._fee_mult

        self._add_to_history(stock, 1, nlongs)

        return True

    # TODO: add leverage
    