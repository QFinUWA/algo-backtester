from .opt._portfolio import Portfolio
from inspect import signature, Parameter
from functools import wraps

class Strategy:

    def __init__(self):
        '''
        # Strategy Base Class
        This is the base class for all strategys. It is not meant to be used directly. Instead, it should be inherited from 
        and the on_data method should be overwritten. The on_data method is called every time the strategy recieves new data.
        The ``on_finish`` is run on the completion of the backtest, and whatever it returns is added to the ``SingleRunResult`` object.
        
        ## Example
        ```python
        class BasicBollinger(Strategy):
    
        def __init__(self, quantity=1):
            self.quantity = quantity
            return
        
        def on_data(self, prices, indicators, portfolio):
            
            # If current price is below lower Bollinger Band, enter a long position
            if(prices['close']['AAPL'][-1] < indicators['lower_bollinger']['AAPL'][-1]):
                portfolio.cover_short('AAPL', quantity=self.quantity)
                portfolio.enter_long('AAPL', quantity=self.quantity)

            # If current price is above upper Bollinger Band, enter a long position   
            if(prices['close']['AAPL'][-1] > indicators['upper_bollinger']['AAPL'][-1]):
                portfolio.sell_long('AAPL', quantity=self.quantity)
                portfolio.enter_short('AAPL', quantity=self.quantity)
        ```
        '''

        return
    
    #---------------[Class Methods]-----------------#
    @classmethod
    def defaults(cls):
  
        return {
                k: v.default
                for k, v in signature(cls.__init__).parameters.items()
                if v.default is not Parameter.empty
            }    
    #---------------[Public Methods]-----------------#
    def run_on_data(self, args: tuple, portfolio: Portfolio) -> None:
        portfolio.curr_prices, *data = args
        self.on_data(*data, portfolio)

    def on_data(self, prices: dict, indicators: dict, portfolio: Portfolio) -> None:
        ...

    def on_finish(self) -> None:
        ...
