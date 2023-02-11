from .opt.portfolio import Portfolio
import inspect
from functools import wraps


class Algorithm:

    def __init__(self):
        self.indicator_parameters = dict()

    @classmethod
    def indicator(cls, func, *args, **kwargs):
        @wraps(func)
        def wrapper_func(*_args, **_kwargs):
            return func(*_args, **_kwargs)
        wrapper_func.indicator = True
        return wrapper_func

    @classmethod
    def indicator_functions(cls):
        # TODO: filter by only functions
        return {k: v for k, v in inspect.getmembers(cls)
                if callable(v) and hasattr(getattr(cls, k), 'indicator') and not k.startswith('__')}

    @classmethod
    def defaults(cls):

        def get_defaults(func): 
            signature = inspect.signature(func)
            return {
                k: v.default
                for k, v in signature.parameters.items()
                if v.default is not inspect.Parameter.empty
            }

        ret = {'algorithm': get_defaults(cls.__init__)}
        ret['indicators'] = dict()
        for name, function in cls.indicator_functions().items():
            ret['indicators'][name] = get_defaults(function)
        return ret

    def set_indicator_params(self, params):
        # TODO raise error if not dict
        self.indicator_parameters.update(params)

    
#    def add_indicator(self, name, func):
#        if not callable(func):
#            raise ValueError(
#                f'add_indicator expects a function, not {type(func)}')
#
#        self._indicator_funcs[name] = func


    def run_on_data(self, args, portfolio):
        portfolio.curr_prices, *data = args
        self.on_data(*data, portfolio)

    # to override
    def on_data(self, prices: dict, indicators: dict, portfolio: Portfolio) -> None:
        return
