
import bokeh.plotting
import bokeh.palettes
import bokeh.models
import os 
import pandas as pd
import numpy as np
from .opt._result import SingleRunResult

class Plotting:

    #---------------[Class Methods]-----------------#
    
    @classmethod
    def plot_result(cls, result: SingleRunResult, show_portfolio: bool=True, stocks: list=[], show_transactions: bool = True, normalise_stocks: bool =True, filename: str = None) -> None:
        '''
        Plots the results of a single run.

        ## Parameters
        - ``result`` (``SingleRunResult``): The result of a single run.
        - ``show_portfolio`` (``bool``): show portfolio value
        - ``stocks`` (``list``): A list of stocks to plot.
        - ``show_transactions`` (``bool``): If ``True`` transaction will be plotted on the respective instrumenets.
        - ``normalise_stocks`` (``bool``): If ``True``, stocks will be normalised to the portfolio value at the start of the run.
        - ``filename`` (``str``): The filename to save the plot to. If ``None``, the plot will be displayed in a browser.

        ## Returns
        ``None``
        '''
        
        p = bokeh.plotting.figure(x_axis_type='linear', title=f"Portfolio Value over Time - {result._datetimeindex.iloc[0]} --> {result._datetimeindex.iloc[-1]}", width=1000, height=400)
        p.grid.grid_line_alpha = 0.3
        p.xaxis.axis_label = 'Date'
        p.yaxis.axis_label = 'Portfolio Value'
        p.xaxis.major_label_overrides = {
            i: date.strftime('%Y-%m-%d %H:%S') for i, date in enumerate(result._datetimeindex)
        }
        
        # -----[plotting portfolio]-----
        value = [sum(result.value[s][i][0] - result.value[s][i][1]for s in stocks) for i in range(len(list(result.value.values())[0]))]
        r = np.array([_ for _ in range(len(value))])
        if show_portfolio:
            p.line(r, value, line_width=2, legend_label='portfolio', color='black')

        # -----[plotting buys and sells]-----
        stock_prices = {stock: result._stockdata[stock]['close'][result._start:result._end] for stock in stocks}
        for stock, prices in stock_prices.items():
            p.line(r, prices, line_width=2, color='blue', legend_label=stock)

        lbuy = {stock: [i for i, s, q in result.buys if s == stock] for stock in stocks}
        lsell = {stock: [i for i, s, q in result.sells if s == stock] for stock in stocks}
        # sbuy = np.array([i for i, *_ in result._shorts['enter']])
        # sclose = np.array([i for i, *_ in result._shorts['exit']])
        SIZE = 4
        if show_transactions:
            
            for stock, prices in stock_prices.items():
                # print(stock, prices[0])
                p.circle(lbuy[stock], np.array([prices.iloc[i] for i in lbuy[stock]]), color='red', size=SIZE, legend_label='buy')
                p.circle(lsell[stock], np.array([prices.iloc[i] for i in lsell[stock]]), color='green', size=SIZE, legend_label='sell')

        bokeh.plotting.show(p)
        if filename:
            bokeh.plotting.output_file(filename)

    @classmethod
    def plot_indicators(cls, indicators, data_folder: str, stocks: list = [], filename: bool=None) -> None:
        '''
        Plot custom indicators over time.

        ## Parameters
        - ``indicators`` (``class``): The indicator class.
        - ``data_folder`` (``str``): The folder containing the stock data.
        - ``stocks`` (``list``): A list of stocks to plot.
        - ``filename`` (``str``): The filename to save the plot to. If ``None``, the plot will be displayed in a browser.

        ## Returns
        ``None``
        '''
        p = bokeh.plotting.figure(x_axis_type="linear", title="Portfolio Value over Time", width=1000, height=400)
        p.grid.grid_line_alpha = 0.3
        p.xaxis.axis_label = 'Time'
        p.yaxis.axis_label = 'Indicator Value'
        

        ind = indicators(stockdata=data_folder)
        in_folder = set([os.listdir(data_folder)[0].split('.')[0]])
        stocks = list(in_folder & set(stocks) if stocks else in_folder)
        # print(os.listdir(data_folder)[0].split('.')[0])

        df = pd.read_csv(os.path.join(data_folder, f'{stocks[0]}.csv'))
        p.xaxis.major_label_overrides = {
            i: date.strftime('%Y-%m-%d %H:%S') for i, date in enumerate(pd.to_datetime(df['time']))
        }
        r = np.array([_ for _ in range(len(df))])

        it = [(stock, *_) for _ in zip(cls._colours(10), *ind.indicator_values().items()) for stock in stocks]

        # "it" is of the form [(stock, colour, name, value), ...]
        data = {'ys': np.array([value[stock] for stock, *_, value in it]),
                'xs': np.array([r for _ in it]),
                'names': np.array([f'{name} ({stock})' for stock, _, name, _ in it]),
                'cols': np.array([col for _, col, *_ in it]),
        }
        source = bokeh.models.ColumnDataSource(data)

        p.multi_line(xs='xs', ys='ys', legend_label='names', cols='cols', line_width=2, source=source)

        bokeh.plotting.show(p)
        if filename:
            bokeh.plotting.output_file(filename)
    
    #---------------[Private Class Methods]-----------------#
    @classmethod
    def _colours(cls, n: int) -> list:
        return bokeh.palettes.Category10[n]