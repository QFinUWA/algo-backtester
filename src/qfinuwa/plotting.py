
import bokeh
import os 
import pandas as pd
import numpy as np

class Plotting:

    @classmethod
    def colours(cls, n):
        return bokeh.palettes.Category10[n]
    
    @classmethod
    def plot_result(cls, result, stocks=list(), transactions_on = 'portfolio', normalise_stocks=True, filename = None):
        p = bokeh.plotting.figure(x_axis_type='linear', title=f"Portfolio Value over Time - {result._datetimeindex.iloc[0]} --> {result._datetimeindex.iloc[-1]}", width=1000, height=400)
        p.grid.grid_line_alpha = 0.3
        p.xaxis.axis_label = 'Date'
        p.yaxis.axis_label = 'Portfolio Value'
        p.xaxis.major_label_overrides = {
            i: date.strftime('%Y-%m-%d %H:%S') for i, date in enumerate(result._datetimeindex)
        }
        # -----[plotting portfolio]-----
        r = [_ for _ in range(len(result.cash))]
        p.line(r, result.cash, line_width=2, legend_label='portfolio', color='black')

        # -----[plotting buys and sells]-----

        for stock in stocks:
            price = result._stockdata[stock]['close'][result._start:result._end]
            l = price*result.cash[0]/price.iloc[0] if normalise_stocks else price
            # print(l)
            p.line(r, l, line_width=2, color='red', legend_label=stock)

        lbuy = [i for i, *_ in result._longs['buy']]
        lsell = [i for i, *_ in result._longs['sell']]
        sbuy = [i for i, *_ in result._shorts['enter']]
        sclose = [i for i, *_ in result._shorts['close']]
        SIZE = 4
        if transactions_on == 'portfolio':
            on = result.cash
        else:
            l = result._stockdata[transactions_on]['close'][result._start:result._end]
            on = np.array(l*result.cash[0]/l.iloc[0] if normalise_stocks else l)

        p.circle(lbuy, [on[i] for i in lbuy], color='red', size=SIZE, legend_label='enter long')
        p.circle(lsell, [on[i] for i in lsell], color='green', size=SIZE, legend_label='sell long')
        p.circle(sbuy, [on[i] for i in sbuy], color='yellow', size=SIZE, legend_label='enter short')
        p.circle(sclose, [on[i] for i in sclose], color='pink', size=SIZE, legend_label='cover short')

        bokeh.plotting.show(p)
        if filename:
            bokeh.plotting.output_file(filename)

    @classmethod
    def plot_indicators(cls, indicators, data_folder, stocks = list(), filename=None):
        

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
        r = [_ for _ in range(len(df))]

        it = [(stock, _) for _ in zip(cls.colours(10), ind.indicator_values().items()) for stock in stocks]

        data = {'ys': [value[stock] for stock, (_, (_, value)) in it],
                'xs': [r for _ in it],
                'names': [f'{name} ({stock})' for stock, (_, (name, _)) in it],
                'cols': [col for _, (col, (_, _)) in it],
        }
        source = bokeh.models.ColumnDataSource(data)

        p.multi_line(xs='xs', ys='ys', legend_label='names', cols='cols', line_width=2, source=source)

        bokeh.plotting.show(p)
        if filename:
            bokeh.plotting.output_file(filename)