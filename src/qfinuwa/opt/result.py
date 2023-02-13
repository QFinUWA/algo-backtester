import itertools
import pandas as pd
import numpy as np
from tabulate import tabulate


class Result:

    def __init__(self, stocks, cash, longs, shorts, datetimeindex):
        
        longs = {stock: [p for _,s,p in longs if s == stock] for stock in stocks}
        shorts = {stock: [p for _,s,p in shorts if s == stock] for stock in stocks}
        self.longs = {k: (len(v), np.mean(v or [0]), np.std(v or [0])) for k,v in longs.items()}
        self.shorts = {k: (len(v), np.mean(v or [0]), np.std(v or [0])) for k,v in shorts.items()}
        self._sdv = {stock: np.std(longs[stock] + shorts[stock]) for stock in stocks}
        self._sdv_longs = np.std([p for *_,p in longs.values()])
        self._sdv_shorts = np.std([p for *_,p in shorts.values()])
        self._sdv_all = np.std([p for *_,p in longs.values()] + [p for *_,p in shorts.values()])

        self.cash = cash
        self.datetimeindex = datetimeindex.reset_index(drop=True)
        self.stocks = stocks

    @property
    def roi(self):
        return self.cash[-1]/self.cash[0] - 1

    @property
    def date_range(self):
        # reset index of self.datetimeindex
       

        return self.datetimeindex.iloc[0].strftime("%m/%d/%Y"), self.datetimeindex.iloc[-1].strftime("%m/%d/%Y")

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
                self.shorts[stock][2]] for stock in self.stocks}, index = [f'{b}_{a}' for a,b in itertools.product(['trades', 'longs', 'shorts'], ["n", 'mean_per', 'std'])])
        
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
    
    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(str(self))

    def __str__(self):
         
        table =  str(tabulate(self.statistics, headers = 'keys', tablefmt="github", showindex = True, numalign="right"))
        return '\n' + ' -> '.join(self.date_range) + f'\n\nROI:\t{self.roi}\n\n' + table



class ResultsContainer:

    def __init__(self, parameters, results):
        a,i = parameters
        self.parameters = {
            'algorithm_paramters': a,
            'indicator_parameters': i
        }

        self.results = results

    def __getitem__(self, key):
        return self.results[key]

    def __iter__(self):
        return iter(self.results)

    # TODO: should this be mean ROI or total ROI?
    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(str(self) )

    @property
    def roi(self):
        return np.mean([result.roi for result in self.results])

    @property
    def statistics(self):
        dfs = [result.statistics for result in self.results]
        df_concat = pd.concat(dfs, axis=0)
        by_row_index = df_concat.groupby(df_concat.index)
        return by_row_index.mean().loc[dfs[0].index, :]

    def __str__(self):
        table = str(tabulate(self.statistics, headers = 'keys', tablefmt="github", showindex = True, numalign="right"))
        return '\n' + str(self.parameters) + f'\n\nMean ROI:\t{self.roi}\n\n' + '\n'.join([(' -> '.join(res.date_range) + f':\t{res.roi:.3f}') for res in self]) +'\n\n'  + table

