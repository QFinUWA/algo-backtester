# QFIN's Algorithmic Backtester (QFAB)

[GitHub Page](https://github.com/QFinUWA/algo-backtester)

## Setup

To install on your system, use pip:

```
pip install qfinuwa
```

## API Class

To pull market data ensure you have a text file with the API key and call ``API.fetch_stocks``:

```py
from qfinuwa import API

path_to_API = 'API_key.txt'
download_folder = './data'

API.fetch_stocks(['AAPL', 'GOOG', 'TSLA'], path_to_API, download_folder)
```

## Indicator Class

#### Multi-Indicators

A multi-indicator takes in a single signal (price of an arbitary stock) and outputs a transformation of that stock.

It is called ``MultiIndicator`` because the indicator will have multiple values (one for each stock)

```py
# Example 

class CustomIndicators(Indicators):
    
    @Indicators.MultiIndicator
    def bollinger_bands(self, stock: pd.DataFrame):
        BOLLINGER_WIDTH = 2
        WINDOW_SIZE = 100
        
        mid_price = (stock['high'] + stock['low']) / 2
        rolling_mid = mid_price.rolling(WINDOW_SIZE).mean()
        rolling_std = mid_price.rolling(WINDOW_SIZE).std()

        return {"upper_bollinger": rolling_mid + BOLLINGER_WIDTH*rolling_std,
                "lower_bollinger": rolling_mid - BOLLINGER_WIDTH*rolling_std}
```


### Single-Indicators

Similar to ``MultiIndicator``, ``SingleIndicator`` is implemented as a function that takes in stock data and returns an indicator or indicators.

It is called ``SingleIndicator`` because there is only a single signal.

```py
# Example 
class CustomIndicators(Indicators):

    @Indicators.SingleIndicator
    def etf(self, stock: dict):

        apple = 0.2
        tsla = 0.5
        goog = 0.3

        return {'etf': apple*stock['AAPL'] + tsla*stock['TSLA'] + goog*stock['GOOG']}
```

### Manually Testing

You can manually test you indicators as follows:

```py

stock_a = pd.from_csv('stockA.csv')
stock_b = pd.from_csv('stockA.csv')

# multi-indicator for stockA (returns dict of dict of pd.Series)
output_a = CustomIndicators.bollinger(stockA)
# multi-indicator for stockB (returns dict of dict of pd.Series)
output_b = CustomIndicators.bollinger(stockA)

# single-indicator for stockA + stockB (returns dict of pd.Series)
output = CustomIndicators.etf({'stockA': stock_a, 'stockB': stock_b})
```

### Hyper-parameters

Each function you implement can be thought of as a hyperparameter "group" that bundles the indicator it returns (the keys to the dictionary the indicator function returns).

The backtester can change hyperparameters for you, but to do so you need to give each one a name, in the form of ``kwargs``.

The ``kwargs`` must include a default value which will be used if you do not specify a value.

```py
class CustomIndicators(Indicators):
    
    @Indicators.MultiIndicator
    def bollinger_bands(self, stock: pd.DataFrame, BOLLINGER_WIDTH = 2, WINDOW_SIZE=100):
        
        mid_price = (stock['high'] + stock['low']) / 2
        rolling_mid = mid_price.rolling(WINDOW_SIZE).mean()
        rolling_std = mid_price.rolling(WINDOW_SIZE).std()

        return {"upper_bollinger": rolling_mid + BOLLINGER_WIDTH*rolling_std,
                "lower_bollinger": rolling_mid - BOLLINGER_WIDTH*rolling_std}

    @Indicators.SingleIndicator
    def etf(self, stock: dict, apple = 0.2, tsla= 0.5, goog=0.3):

        return {'etf': apple*stock['AAPL'] + tsla*stock['TSLA'] + goog*stock['GOOG']}
```

## Strategy Class

To define your strategy extend ``qfin.Strategy`` to inherit its functionalities. Implement your own ``on_data`` function.

Your ``on_data`` function will be expected to take 4 positional arguments.
- ``self``: reference to this object
- ``prices``: a dictionary of numpy arrays of historical prices
- ``portfolio``: object that manages positions

Similar to ``qfin.Indicators``, you can define hyperparameters for your model in ``__init__``.

```py
# Example Strategy
class BasicBollinger(Strategy):

    def __init__(self, quantity=5):
        self.quantity = quantity
        self.n_failed_orders = 0
    
    def on_data(self, prices, indicators, portfolio):

        # If current price is below lower Bollinger Band, enter a long position
        for stock in portfolio.stocks:

            if(prices['close'][stock][-1] < indicators['lower_bollinger'][stock][-1]):
                order_success = portfolio.order(stock, quantity=self.quantity)
                if not order_success:
                    self.n_failed_orders += 1
            
            # If current price is above upper Bollinger Band, enter a short position
            if(prices['close'][stock][-1] > indicators['upper_bollinger'][stock][-1]):
                order_success = portfolio.order(stock, quantity=-self.quantity)
                if not order_success:
                    self.n_failed_orders += 1

    def on_finish(self):
        # Added to results object - access using result.on_finish
        return self.n_failed_orders
```
Additionally, you can specify a function ``on_finish`` that will run on the completion of a run, if you want to save your own data. Whatever this function returns will can be accessed in the results (see ``SingleRunResults.on_finish``).
## Backtester Class

The ``Backtester`` class asks for a custom strategy, custom indicators and data from the user. Once created, it can run multiple backtests without having to recalculate the indicators - when used in a Notebook environment the backtester object can persist and incrementally updated with new values.

### Creating a Backtester

See ``qfinuwa.Backtester`` docstrings for specifics.


```py
from qfinuwa import Backtester

backtester = Backtester(CustomStrategy, CustomIndicators, 
                        data=r'\data', days=90, 
                        delta_limits=1000, fee=0.01)
```

## Updating Indicator Parameters

### Update Parameters

```py
backtester.indicators.update_params(dict_of_updates)
```

### Get Current Parameters

```py
backtester.indicators.params
```

### Get Defaults

```py
backtester.indicators.defaults
```

### Updating Class

```py
backtester.indicators = NewIndicatorClass
```

## Updating Strategy Parameters

### Update Parameters

```py
backtester.strategy.update_params(dict_of_updates)
```

### Get Current Parameters

```py
backtester.strategy.params
```

### Get Defaults

```py
backtester.strategy.defaults
```

### Updating  Class

```py
backtester.strategy = NewStrategyClass
```
## Running a Backtester

## Time Complexity Analysis 

![Time scaling of Backtester.__init__](./imgs/__init__.png?raw=true)

![Time scaling of Backtester.run](./imgs/run.png?raw=true)
