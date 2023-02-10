import heapq
from prettytable import PrettyTable


class Portfolio:

    def __init__(self, stocks: list, cash: float, fee: float):

        self._curr_prices = None

        self._i = -1
        self._cash = cash
        # TODO: arg checking
        self._fee_mult, self._fee_div = 1 + fee, 1 - fee
        self._stocks = stocks
        self._stock_to_id = {stock: i for i, stock in enumerate(stocks)}

        # self._short_value = 0
        self._longs = {stock: [] for stock in stocks}
        # maybe make a heap or linked list??
        self._shorts = {stock: [] for stock in stocks}


        self._cash_history = []

        self.long_stats = []
        self.short_stats = []       


    @property
    def stocks(self):
        return self._stocks
        
    @property
    def curr_prices(self):
        return self._curr_prices

    @curr_prices.setter
    def curr_prices(self, prices: dict):
        self._i += 1
        self._curr_prices = prices

        v_shorts = -1*sum(2*cos + self._fee_mult * q* self._curr_prices[stock] for stock in self._shorts for cos, q in self._shorts[stock])
        v_longs = self._fee_div *sum( q * self._curr_prices[stock] for stock in self._longs for  _, q in self._longs[stock])
        # print(f'cash: {self._cash}, v_longs: {v_longs}, v_shorts: {v_shorts}')
        self._cash_history.append(self._cash + v_longs + v_shorts)

    @property
    def cash(self):
        return self._cash

    @cash.setter
    def cash(self, _):
        raise ValueError('Cannot modify Portfolio.cash ... you cheeky bugger')

    @property
    def history(self):
        return (self._cash_history, self.long_stats, self.short_stats)


    def __str__(self):
        t = PrettyTable(['Stock', 'Longs', 'Shorts'])
        for stock in self._stocks:
            # print([stock, self._longs[stock], sum(q for _, q in self._shorts[stock])])
            t.add_row([stock, self._longs[stock], sum(q for _, q in self._shorts[stock])])
            
        return f'${self._cash}\n' + str(t)

    def enter_long(self,  stock: str, quantity: float=None, cost: float=None) -> int:

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

        heapq.heappush(self._longs[stock], (cost, quantity))

        return 1

    def sell_long(self,  stock: str, quantity: float=None, price: float=None) -> int:

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
            return 0
        ## -----
        
        self._cash += total_pay
        self.long_stats.append((self._i, stock, total_pay - total_cost))
        
        return 1

    def enter_short(self, stock: str, quantity: float=None, cost: float=None) -> int:

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

        self._cash -= price

        heapq.heappush(self._shorts[stock], (-price, quantity))

        return 1

    def cover_short(self, stock: str, quantity: float=None, cost: float=None) -> int:

        bool_quantity, bool_cost = bool(quantity), bool(cost)

        if not bool_quantity ^ bool_cost:
            raise TypeError('Please input quanity OR cost.')
  
        cost_to_buy = 0
        deposit = 0
        
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
