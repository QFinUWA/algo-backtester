from itertools import chain, product
from pandas import concat, DataFrame, DatetimeIndex
import numpy as np
from tabulate import tabulate

class SingleRunResult:

    def __init__(self, stocks: list, stockdata, 
            datetimeindex: DatetimeIndex, startend: tuple, 
            value: dict, trades: list, on_finish: object):
        self._start, self._end = startend

        datetimeindex = datetimeindex[self._start: self._end]

        self.buys = [(i,s,q) for i, s,q in trades if q > 0]
        self.sells = [(i, s,-q) for i,s,q in trades if q < 0]

        self.n_buys = {stock: len([q for i,s,q in self.buys if s == stock]) for stock in stocks}
        self.n_sells = {stock: len([-q for i,s,q in self.sells if s == stock]) for stock in stocks}
        self.gross_pnl = {stock: value[stock][-1][0] for stock in stocks}
        self.fees_paid = {stock: value[stock][-1][1] for stock in stocks}
        self.net_pnl = {stock: value[stock][-1][0] - value[stock][-1][1]  for stock in stocks}

        self.value = value
        self._datetimeindex = datetimeindex.reset_index(drop=True)
        self._stocks = stocks

        self._stockdata = stockdata._stock_df

        self.on_finish = on_finish

    #---------------[Properties]-----------------#
    @property
    def roi(self):
        return sum(self.net_pnl.values())

    @property
    def date_range(self):
        # reset index of self.datetimeindex
        return self._datetimeindex.iloc[0].strftime("%d/%m/%Y"), self._datetimeindex.iloc[-1].strftime("%d/%m/%Y")

    @property
    def statistics(self):

        df = DataFrame({stock: [
                self.n_buys[stock] + self.n_sells[stock],
                self.n_buys[stock],
                self.n_sells[stock],
                self.gross_pnl[stock],
                self.fees_paid[stock],
                self.net_pnl[stock],
                0 if self.n_buys[stock] + self.n_sells[stock] == 0 else self.net_pnl[stock]/(self.n_buys[stock] + self.n_sells[stock]),
                    ] for stock in self._stocks}, 
                    index = ['n_trades', 'n_buys', 'n_sells', 'gross_pnl', 'fees_paid', 'net_pnl', 'pnl_per_trade'])
        
        df['Net'] = [ df.iloc[0, :].sum(),
                        df.iloc[1, :].sum(),
                        df.iloc[2, :].sum(),
                        df.iloc[3, :].sum(),
                        df.iloc[4, :].sum(),
                        df.iloc[5, :].sum(),
                        sum(self.net_pnl.values())/(sum(self.n_buys.values()) + sum(self.n_sells.values())),
                        ]

        return df
    
    def save(self, filename: str):
        with open(filename, 'w') as f:
            f.write(str(self))

    def __str__(self):
        table =  str(tabulate(self.statistics, headers = 'keys', tablefmt="github", showindex = True, numalign="right"))
        return '\n' + ' -> '.join(self.date_range) + f'\n\nROI:\t{self.roi}\n\n' +  'RUN RESULTS:\n' + table

    def __repr__(self) -> str:
        return self.__str__()


class MultiRunResult:

    def __init__(self, parameters: dict, results: list):
        a,i = parameters
        self.parameters = {
            'strategy': a,
            'indicator': i,
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
        return '\n' + str(self.parameters) + f'\n\nMean ROI:\t{self.roi[0]}\nSTD ROI:\t{self.roi[1]}\n\n' + \
              '\n'.join([(' -> '.join(res.date_range) + f':\t{res.roi:.3f}') for res in self]) \
                +'\n\n'  + f'AVERAGED RESULTS FOR {len(self.results)} RUNS:\n' + table

    def __repr__(self) -> str:
        return self.__str__()

class ParameterSweepResult:

    def __init__(self, multi_results: MultiRunResult, params: dict):

        # a = dict()
        # i = dict()
        # for result in multi_results:

        #     for para, val in result.parameters['strategy'].items():
        #         a[para] = sorted(a.get(para, []) + [str(val)])

        #     for indic, params in result.parameters['indicator'].items():
        #         i[indic] = i.get(indic, dict())

        #         for para, val in params.items():
        #             i[indic][para] = sorted(i[indic].get(para, []) + [str(val)])

        self.parameters = params

        self.results = sorted(multi_results, key=lambda res: -res.roi[0])

    #---------------[Properties]-----------------#
    @property
    def best(self):
        return self.results[0]

    #----------------[Public Methods]-----------------#
    def save(self, filename: str):
        with open(filename, 'w') as f:
            f.write(str(self) )
        # TODO: add big dataframe of all results
    
    #---------------[Internal Methods]-----------------#
    def __getitem__(self, idx):

        return self.results[idx]

    def __iter__(self):
        return self.results.__iter__()

    def __str__(self):
        # TODO: make look better
        return f'Best parameter results:\n{repr(self.best)}'

    def __repr__(self):
        return self.__str__()