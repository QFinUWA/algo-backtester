from itertools import chain, product
from pandas import concat, DataFrame, DatetimeIndex
import numpy as np
from tabulate import tabulate

class SingleRunResult:

    def __init__(self, stocks: list, stockdata, 
            datetimeindex: DatetimeIndex, startend: tuple, 
            cash: float, longs: list, shorts: list, to_add: object):
        self._start, self._end = startend

        datetimeindex = datetimeindex[self._start: self._end]

        self._longs = longs
        self._shorts = shorts 

        longs = {stock: [p for _,s,p in longs['exit'] if s == stock] for stock in stocks}
        shorts = {stock: [p for _,s,p in shorts['exit'] if s == stock] for stock in stocks}
        self.longs = {k: (len(v), np.mean(v or [0]), np.std(v or [0])) for k,v in longs.items()}
        self.shorts = {k: (len(v), np.mean(v or [0]), np.std(v or [0])) for k,v in shorts.items()}
        self._sdv = {stock: np.std(longs[stock] + shorts[stock] or [0]) for stock in stocks}

        std_longs = list(chain.from_iterable(longs[s] or [0] for s in longs))
        std_shorts = list(chain.from_iterable(shorts[s] or [0] for s in shorts))
        self._sdv_longs = np.std(std_longs)
        self._sdv_shorts = np.std(std_shorts )
        self._sdv_all = np.std(np.concatenate([std_longs, std_shorts]))

        self.cash = cash
        self._datetimeindex = datetimeindex.reset_index(drop=True)
        self._stocks = stocks

        self._stockdata = stockdata._stock_df

        if to_add is not None:
            self.data = to_add

    #---------------[Properties]-----------------#
    @property
    def roi(self):
        return self.cash[-1]/self.cash[0] - 1

    @property
    def date_range(self):
        # reset index of self.datetimeindex
        return self._datetimeindex.iloc[0].strftime("%m/%d/%Y"), self._datetimeindex.iloc[-1].strftime("%m/%d/%Y")

    @property
    def statistics(self):

        df = DataFrame({stock: [
                self.longs[stock][0] + self.shorts[stock][0],
                (self.longs[stock][1] + self.shorts[stock][1])/2,
                self._sdv[stock],
                self.longs[stock][0],
                self.longs[stock][1],
                self.longs[stock][2],
                self.shorts[stock][0],
                self.shorts[stock][1],
                self.shorts[stock][2]] for stock in self._stocks}, index = [f'{b}_{a}' for a,b in product(['trades', 'longs', 'shorts'], ["n", 'mean_per', 'std'])])
        
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
    
    def save(self, filename: str):
        with open(filename, 'w') as f:
            f.write(str(self))

    def __str__(self):
        table =  str(tabulate(self.statistics, headers = 'keys', tablefmt="github", showindex = True, numalign="right"))
        return '\n' + ' -> '.join(self.date_range) + f'\n\nROI:\t{self.roi}\n\n' + table

    def __repr__(self) -> str:
        return self.__str__()


class MultiRunResult:

    def __init__(self, parameters: dict, results: list):
        a,i = parameters
        self.parameters = {
            'strategy': a,
            'indicator': i
        }

        self.results = results

    def __getitem__(self, key: int):
        return self.results[key]

    def __iter__(self):
        return self.results.__iter__()

    # TODO: should this be mean ROI or total ROI?
    def save(self, filename: str):
        with open(filename, 'w') as f:
            f.write(str(self) )

    #---------------[Properties]-----------------#
    @property
    def roi(self):
        rois = [result.roi for result in self.results]
        return (np.mean(rois), np.std(rois))
    

    @property
    def statistics(self):
        dfs = [result.statistics for result in self.results]
        df_concat = concat(dfs, axis=0)
        by_row_index = df_concat.groupby(df_concat.index)
        return by_row_index.mean().loc[dfs[0].index, :]

    def __str__(self):
        table = str(tabulate(self.statistics, headers = 'keys', tablefmt="github", showindex = True, numalign="right"))
        return '\n' + str(self.parameters) + f'\n\nMean ROI:\t{self.roi[0]}\nSTD ROI:\t{self.roi[1]}\n\n' + '\n'.join([(' -> '.join(res.date_range) + f':\t{res.roi:.3f}') for res in self]) +'\n\n'  + table

    def __repr__(self) -> str:
        return self.__str__()

class ParameterSweepResult:

    def __init__(self, multi_results: MultiRunResult):

        a = dict()
        i = dict()
        for result in multi_results:

            for para, val in result.parameters['strategy'].items():
                a[para] = sorted(a.get(para, []) + [str(val)])

            for indic, params in result.parameters['indicator'].items():
                i[indic] = i.get(indic, dict())

                for para, val in params.items():
                    i[indic][para] = sorted(i[indic].get(para, []) + [str(val)])


        self.parameters = {
            'strategy_paramters': a,
            'indicator_parameters': i
        }

        self.container_results = multi_results

    #---------------[Properties]-----------------#
    @property
    def best(self):
        return max(self.container_results, key=lambda res: res.roi[0])

    #----------------[Public Methods]-----------------#
    def save(self, filename: str):
        with open(filename, 'w') as f:
            f.write(str(self) )
        # TODO: add big dataframe of all results
    
    #---------------[Internal Methods]-----------------#
    def __getitem__(self, idx):

        return self.container_results[idx]

    def __iter__(self):
        return self.container_results.__iter__()

    def __str__(self):

        # TODO: make look better
        return f'Best parameter results:\n{repr(self.best)}'
