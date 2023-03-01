from .opt.portfolio import Portfolio
from inspect import signature, Parameter


class Algorithm:

    def __init__(self):
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
    def on_data(self, prices: dict, indicators: dict, portfolio: Portfolio) -> None:
        return

    def run_on_data(self, args: tuple, portfolio: Portfolio) -> None:
        portfolio.curr_prices, *data = args
        self.on_data(*data, portfolio)

    def on_finish(self, portfolio: Portfolio) -> None:
        raise NotImplementedError
