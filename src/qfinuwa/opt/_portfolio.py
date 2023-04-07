
from tabulate import tabulate

class Portfolio:

    # buy long, se
    def __init__(self, stocks: list, delta_limits: dict, fee: float):

        self._curr_prices = None

        self._i = -1
        # self._cash = cash
        # TODO: arg checking
        # self._fee_mult, self._fee_div = 1 + fee, 1 - fee
        self._fee = fee
        self._stocks = stocks
        self._stock_to_id = {stock: i for i, stock in enumerate(stocks)}

        # self._short_value = 0
        # self._longs = {stock: [] for stock in stocks}
        # self._n_longs = {stock: 0 for stock in stocks}
        # self._shorts = {stock: [] for stock in stocks}
        # self._n_shorts = {stock: 0 for stock in stocks}

        self._cash_history = {stock: [] for stock in stocks}

        # self._long_stats = {'enter': [], 'exit': []}
        # self._short_stats = {'enter': [], 'exit': []}   

        self._delta = {stock: 0 for stock in stocks}   
        self._delta_limits = delta_limits 
        # print('s', stocks)
        self._fees_paid = {stock: 0 for stock in stocks}  
        self._trades = []

        # TODO: add delta history 

    #---------------[Properties]-----------------#
    @property
    def stocks(self):
        return self._stocks

    # @property
    # def holdings(self):
    #     return {'longs': self._n_longs, 'shorts': self._n_shorts}
    
    @property
    def delta(self):
        return self._delta
        
    @property
    def curr_prices(self):
        return self._curr_prices

    @curr_prices.setter
    def curr_prices(self, prices: dict):
        self._i += 1
        self._curr_prices = prices

        # v_shorts = -1*sum(2*cos + self._fee_mult * q* self._curr_prices[stock] for stock in self._shorts for cos, q in self._shorts[stock])
        # v_longs = self._fee_div *sum( q * self._curr_prices[stock] for stock in self._longs for  _, q in self._longs[stock])
        for s in self._stocks:
            self._cash_history[s].append(self._delta[s]*self._curr_prices[s] - self._fees_paid[s])

    # @property
    # def cash(self):
    #     return self._cash

    # @cash.setter
    # def cash(self, _):
    #     raise ValueError('Cannot modify Portfolio.cash ... you cheeky bugger')

    #---------------[Public Methods]-----------------#

    def order(self, stock: str, quantity: int) -> bool:
        
        if abs(self._delta[stock] + quantity) > self._delta_limits[stock]:
            return False 

        self._delta[stock] += quantity
        self._fees_paid[stock] += abs(self._fee*quantity*self._curr_prices[stock])
        self._trades.append((self._i, stock, quantity))
        return True
    

    # def enter_position(self, direction: str,  stock: str, quantity: float=None, value: float=None) -> int:
    #     quantity_bool = quantity is not None
    #     cost_bool = value is not None
    #     if not quantity_bool ^ cost_bool:
    #         raise TypeError('Please input quanity OR cost.')
        
    #     try:
    #         if direction == 'long':
    #             ##
    #             if cost_bool:
    #                 quantity = value*self._fee_div/self._curr_prices[stock]
                
    #             ##
    #             elif quantity_bool:
    #                 value = quantity*self._curr_prices[stock]*self._fee_mult

    #             if value > self._cash:
    #                 return 1
    #             self._cash -= value

    #             self._n_longs[stock] += quantity
    #             heapq.heappush(self._longs[stock], (value, quantity))
    #             self._long_stats['enter'].append((self._i, stock, quantity))

    #         elif direction == 'short':
    #             ##
    #             if cost_bool:
    #                 quantity = value*self._fee_div/self._curr_prices[stock]

    #             ##
    #             elif quantity_bool:
    #                 value = quantity*self._curr_prices[stock]*self._fee_mult

    #             # TODO: fix to be -delta
    #             if value > self._cash:
    #                 return 1

    #             self._cash -= value

    #             self._n_shorts[stock] += quantity
    #             heapq.heappush(self._shorts[stock], (-value, quantity))
    #             self._short_stats['enter'].append((self._i, stock, quantity))
 
    #     except Exception as e:
    #         return 2
        
    #     return 0

    # def exit_position(self, direction: str,  stock: str, quantity: float=None, value : float=None) -> int:

    #     quantity_bool = quantity is not None
    #     price_bool = value is not None

    #     if not quantity_bool ^ price_bool:
    #         raise TypeError('Please input quanity OR cost.')
    #     try:
    #         if direction == 'long':

    #             ##
    #             if price_bool:
    #                 quantity = value*self._fee_div/self._curr_prices[stock]

    #             ##
    #             elif quantity_bool:
    #                 value = quantity*self._curr_prices[stock]*self._fee_div

    #             ## --------
    #             abs_rem = abs_rem_original = quantity if quantity_bool else value
    #             total_pay, total_cost = 0, 0

    #             while self._longs[stock]:
    #                 # no more shorts to sell
    #                 if abs_rem == 0:
    #                     break

    #                 cos, quant = self._longs[stock][0]

    #                 # quantity we are decreasing to 0 - if quantity is specified 
    #                 # we want to keep closing positions until rem_quanity is 0,
    #                 # same for cost - this is a more consice and neater way to 
    #                 # do this but could also use an if else pattern with repitition 
    #                 abs_amount = quant if quantity_bool else cos

    #                 # cannot sell whole position - sell franction
    #                 if abs_amount > abs_rem:
    #                     frac = abs_rem/abs_amount
                        
    #                     self._longs[stock][0] = cos*(frac-1), quant*(1-frac)
    #                     self._n_longs[stock] -= quant*(1-frac)
    #                     total_cost += frac*cos
    #                     total_pay += frac*quant*self._curr_prices[stock]
    #                     abs_rem = 0
    #                     break

    #                 heapq.heappop(self._longs[stock])

    #                 abs_rem -= abs_amount
    #                 total_cost += cos
    #                 total_pay += quant*self._curr_prices[stock]
    #                 self._n_longs[stock] -= quant
                    
    #             if abs_rem != abs_rem_original:
    #                 self._cash += total_pay
    #                 self._long_stats['exit'].append((self._i, stock, total_pay - total_cost))
                
    #         elif direction == 'short':
        
    #             cost_to_buy = deposit = 0
                
    #             abs_rem = abs_rem_original = quantity if quantity_bool else value
    #             while self._shorts[stock]:
    #                 # no more shorts to sell
    #                 if abs_rem == 0:
    #                     break

    #                 cos, quant = self._shorts[stock][0]

    #                 cos *= -1

    #                 # quantity we are decreasing to 0 - if quantity is specified 
    #                 # we want to keep closing positions until rem_quanity is 0,
    #                 # same for cost - this is a more consice and neater way to 
    #                 # do this but could also use an if else pattern with repitition 
    #                 abs_amount = quant if quantity_bool else cos

    #                 # cannot sell whole position - sell franction
    #                 if abs_amount > abs_rem:
    #                     frac = abs_rem/abs_amount
                        
    #                     self._shorts[stock][0] = cos*(frac-1), quant*(1-frac)

    #                     deposit += frac*cos
    #                     cost_to_buy += frac*quant*self._curr_prices[stock]
    #                     self._n_shorts[stock] -= frac*quant
    #                     abs_rem = 0
    #                     break

    #                 heapq.heappop(self._shorts[stock])

    #                 abs_rem -= abs_amount
    #                 deposit += cos
    #                 cost_to_buy += quant*self._curr_prices[stock]
    #                 self._n_shorts[stock] -= quant

    #             if abs_rem != abs_rem_original:

    #                 profit = deposit - self._fee_mult*cost_to_buy 
    #                 self._cash += profit + deposit

    #                 self._short_stats['exit'].append((self._i, stock, profit))
               
    #     except Exception as e:
    #         return 2
    #     return 0

        
    def wrap_up(self):
        # l_remaining  = {stock: sum(q for _,q in self._longs[stock]) for stock in self._stocks}
        # s_remaining = {stock: sum(q for _,q in self._shorts[stock]) for stock in self._stocks}

        for stock in self._stocks:
            # self.exit_position('long', stock, quantity=l_remaining[stock])
            # self.exit_position('short', stock, quantity=s_remaining[stock])
            self.order(stock, -self._delta[stock])
        return (self._cash_history, self._fees_paid, self._trades)
    

    #---------------[Internal Methods]-----------------#
    def __str__(self):
        table = str(tabulate(list(self._delta.items()), 
                                headers = ['Stock', 'Delta'],
                                tablefmt="grid"))
        return f'CASH:\t${self._cash:.2f}\nFEES PAID:\t${sum(self._fees_paid.values()):.2f}\n' + table 