
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
    def plot_result(cls, result: SingleRunResult, stocks: list=[], transactions_on: str = None, normalise_stocks: bool =True, filename: str = None) -> None:
        '''
        Plots the results of a single run.

        ## Parameters
        - ``result`` (``SingleRunResult``): The result of a single run.
        - ``stocks`` (``list``): A list of stocks to plot.
        - ``transactions_on`` (``str``): The stock to plot transactions on. If ``portfolio``, transactions will be plotted on the portfolio value.
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
        r = np.array([_ for _ in range(len(result.cash))])
        p.line(r, result.cash, line_width=2, legend_label='portfolio', color='black')

        # -----[plotting buys and sells]-----

        for stock in stocks:
            price = result._stockdata[stock]['close'][result._start:result._end]
            l = price*result.cash[0]/price.iloc[0] if normalise_stocks else price
            # print(l)
            p.line(r, l, line_width=2, color='red', legend_label=stock)

        lbuy = np.array([i for i, *_ in result._longs['enter']])
        lsell = np.array([i for i, *_ in result._longs['exit']])
        sbuy = np.array([i for i, *_ in result._shorts['enter']])
        sclose = np.array([i for i, *_ in result._shorts['exit']])
        SIZE = 4
        if transactions_on:
            if transactions_on == 'portfolio':
                on = result.cash
            else:
                l = result._stockdata[transactions_on]['close'][result._start:result._end]
                on = np.array(l*result.cash[0]/l.iloc[0] if normalise_stocks else l)

            p.circle(lbuy, np.array([on[i] for i in lbuy]), color='red', size=SIZE, legend_label='enter long')
            p.circle(lsell, np.array([on[i] for i in lsell]), color='green', size=SIZE, legend_label='sell long')
            p.circle(sbuy, np.array([on[i] for i in sbuy]), color='yellow', size=SIZE, legend_label='enter short')
            p.circle(sclose, np.array([on[i] for i in sclose]), color='pink', size=SIZE, legend_label='cover short')

        bokeh.plotting.show(p)
        if filename:
            bokeh.plotting.output_file(filename)

    @classmethod
    def plot_indicators(cls, indicators: str, data_folder: str, stocks: list = [], filename: bool=None) -> None:
        '''
        Plot custom indicators over time.

        ## Parameters
        - ``indicators`` (``str``): The name of the indicator class.
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