import itertools
import pandas as pd
import numpy as np
from tabulate import tabulate
import bokeh.plotting

class Result:

    def __init__(self, stocks, stockdata, datetimeindex, startend, cash, llongs, sshorts):
        self._start, self._end = startend

        datetimeindex = datetimeindex[self._start: self._end]

        self._longs = llongs
        self._shorts = sshorts 

        longs = {stock: [p for _,s,p in llongs['sell'] if s == stock] for stock in stocks}
        shorts = {stock: [p for _,s,p in sshorts['close'] if s == stock] for stock in stocks}
        self.longs = {k: (len(v), np.mean(v or [0]), np.std(v or [0])) for k,v in longs.items()}
        self.shorts = {k: (len(v), np.mean(v or [0]), np.std(v or [0])) for k,v in shorts.items()}
        self._sdv = {stock: np.std(longs[stock] + shorts[stock] or [0]) for stock in stocks}

        std_longs= np.array([longs[s] or [0] for s in longs]).flatten()
        std_shorts = np.array([shorts[s] or [0] for s in shorts]).flatten()
        self._sdv_longs = np.std(std_longs)
        self._sdv_shorts = np.std(std_shorts )
        self._sdv_all = np.std(np.concatenate([std_longs, std_shorts]))

        self.cash = cash
        self._datetimeindex = datetimeindex.reset_index(drop=True)
        self._stocks = stocks

        self._stockdata = stockdata

    @property
    def roi(self):
        return self.cash[-1]/self.cash[0] - 1

    @property
    def date_range(self):
        # reset index of self.datetimeindex
        return self._datetimeindex.iloc[0].strftime("%m/%d/%Y"), self._datetimeindex.iloc[-1].strftime("%m/%d/%Y")

    @property
    def statistics(self):

        df = pd.DataFrame({stock: [
                self.longs[stock][0] + self.shorts[stock][0],
                (self.longs[stock][1] + self.longs[stock][1])/2,
                self._sdv[stock],
                self.longs[stock][0],
                self.longs[stock][1],
                self.shorts[stock][2],
                self.longs[stock][0],
                self.longs[stock][1],
                self.shorts[stock][2]] for stock in self._stocks}, index = [f'{b}_{a}' for a,b in itertools.product(['trades', 'longs', 'shorts'], ["n", 'mean_per', 'std'])])
        
        df['Net'] = [ df.iloc[0, :].sum(),
                        df.iloc[1, :].mean(),
                        self._sdv_all,
                        df.iloc[3, :].sum(),
                        df.iloc[4, :].mean(),
                        self._sdv_longs,
                        df.iloc[6, :].sum(),
                        df.iloc[7, :].mean(),
                        self._sdv_shorts]

        return df

    def plot(self, stocks = None, filename = None):
        p = bokeh.plotting.figure(x_axis_type="datetime", title="Portfolio Value over Time", width=1000, height=400)
        p.grid.grid_line_alpha = 0.3
        p.xaxis.axis_label = 'Date'
        p.yaxis.axis_label = 'Portfolio Value'
        
        # -----[plotting portfolio]-----
        p.line(self._datetimeindex, self.cash, line_width=2)

        # -----[plotting buys and sells]-----
        for long in self._longs['buy']:
            p.circle(self._datetimeindex[long[0]], self.cash[long[0]], color='red', size=8)
        for long in self._longs['sell']:
            p.circle(self._datetimeindex[long[0]], self.cash[long[0]], color='green', size=8)

        for short in self._shorts['enter']:
            p.circle(self._datetimeindex[short[0]], self.cash[short[0]], color='blue', size=8)
        for short in self._shorts['close']:
            p.circle(self._datetimeindex[short[0]], self.cash[short[0]], color='orange', size=8)

        for stock in stocks or []:
            if stock not in self._stocks:
                raise ValueError(f'{stock} not in portfolio')


            p.line(self._datetimeindex, self._stockdata._stock_df[stock]['close'][self._start:self._end], line_width=2, color='red', legend_label=stock)

        bokeh.plotting.show(p)
        if filename:
            bokeh.plotting.output_file(filename)
    
    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(str(self))

    def __str__(self):
         
        table =  str(tabulate(self.statistics, headers = 'keys', tablefmt="github", showindex = True, numalign="right"))
        return '\n' + ' -> '.join(self.date_range) + f'\n\nROI:\t{self.roi}\n\n' + table

    def __repr__(self) -> str:
        pass


class ResultsContainer:

    def __init__(self, parameters, results):
        a,i = parameters
        self.parameters = {
            'algorithm': a,
            'indicator': i
        }

        self.results = results

    def __getitem__(self, key):
        return self.results[key]

    def __iter__(self):
        return self.results.__iter__()

    # TODO: should this be mean ROI or total ROI?
    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(str(self) )

    @property
    def roi(self):
        rois = [result.roi for result in self.results]
        return (np.mean(rois), np.std(rois))

    @property
    def statistics(self):
        dfs = [result.statistics for result in self.results]
        df_concat = pd.concat(dfs, axis=0)
        by_row_index = df_concat.groupby(df_concat.index)
        return by_row_index.mean().loc[dfs[0].index, :]

    def __str__(self):
        table = str(tabulate(self.statistics, headers = 'keys', tablefmt="github", showindex = True, numalign="right"))
        return '\n' + str(self.parameters) + f'\n\nMean ROI:\t{self.roi[0]}\nSTD ROI:\t{self.roi[1]}\n\n' + '\n'.join([(' -> '.join(res.date_range) + f':\t{res.roi:.3f}') for res in self]) +'\n\n'  + table


class SweepResults:

    def __init__(self, container_results):

        a = dict()
        i = dict()
        for result in container_results:

            for para, val in result.parameters['algorithm'].items():
                a[para] = sorted(a.get(para, []) + [str(val)])

            for indic, params in result.parameters['indicator'].items():
                i[indic] = i.get(indic, dict())

                for para, val in params.items():
                    i[indic][para] = sorted(i[indic].get(para, []) + [str(val)])


        self.parameters = {
            'algorithm_paramters': a,
            'indicator_parameters': i
        }

        self.container_results = container_results

    @property
    def best(self):
        return max(self.container_results, key=lambda res: res.roi[0])

    # TODO: add big dataframe of all results
    
    def __getitem__(self, idx):

        return self.container_results[idx]

    def __iter__(self):
        return self.container_results.__iter__()

    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(str(self) )

    def __str__(self):

        # TODO: make look better

        return f'Best parameter results:\n{repr(self.best)}'
