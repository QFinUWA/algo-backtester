from typing import Union
from tabulate import tabulate

class Portfolio:

    # buy long, se
    def __init__(self, stocks: list, delta_limits: dict, fee: float):

        self._curr_prices = None

        self._i = -1

        self._fee = fee
        self._stocks = stocks
        self._stock_to_id = {stock: i for i, stock in enumerate(stocks)}


        self._delta_limits = delta_limits

        self._value = {stock: [] for stock in stocks}
        self._delta = {stock: 0 for stock in stocks}   
        self._fees_paid = {stock: 0 for stock in stocks}  
        self._capital = {stock: 0 for stock in stocks}  

        self._trades = []

        # TODO: add delta history 

    #---------------[Properties]-----------------#
    @property
    def stocks(self):
        return self._stocks
    
    @property
    def delta(self):
        return self._delta
    
    @property
    def delta_limits(self):
        return self._delta_limits
        
    @property
    def curr_prices(self):
        return self._curr_prices

    @curr_prices.setter
    def curr_prices(self, prices: dict):
        self._i += 1
        self._curr_prices = prices

        for s in self._stocks:
            self._value[s].append((self._delta[s]*self._curr_prices[s] + self._capital[s], self._fees_paid[s]))

    #---------------[Public Methods]-----------------#

    def order(self, stock: str, quantity: Union[int, float]) -> bool:
        
        if abs(self._delta[stock] + quantity) > self._delta_limits[stock]:
            return False 
        
        if quantity == 0:
            return False

        self._delta[stock] += quantity
        price = quantity*self._curr_prices[stock]
        self._fees_paid[stock] += abs(self._fee*price)
        self._capital[stock] -= price
        self._trades.append((self._i, stock, quantity))
        return True
    
        
    def wrap_up(self):
        for stock in self._stocks:
            self.order(stock, -self._delta[stock])
        return (self._value,  self._trades)
    

    #---------------[Internal Methods]-----------------#
    def __str__(self):
        table = str(tabulate(list(self._delta.items()), 
                                headers = ['Stock', 'Delta'],
                                tablefmt="grid"))
        return f'CASH:\t${self._cash:.2f}\nFEES PAID:\t${sum(self._fees_paid.values()):.2f}\n' + table 