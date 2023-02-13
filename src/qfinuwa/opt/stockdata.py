import numpy as np
import pandas as pd
import os
from itertools import product

from IPython import get_ipython

try:
    shell = get_ipython().__class__.__name__
    if shell in ['ZMQInteractiveShell']:
        from tqdm import tqdm_notebook as tqdm   # Jupyter notebook or qtconsole or Terminal running IPython  
    else:
        from tqdm import tqdm   
except NameError:
    from tqdm import tqdm      # Probably standard Python interpreter

class StockData:

    def __init__(self, stocks, data, verbose=False):

        self._indicators = ['open', 'close', 'high', 'low', 'volume']
        self._i = 0

        self._stock_df = dict()

        self._L = 0
        self._index = None

        self._verbose = verbose

        if not verbose:
            print('> Fetching data')
        for stock in (tqdm(stocks, desc='> Fetching data') if verbose else stocks):

            _df = pd.read_csv(os.path.join(data, f'{stock}.csv'))
            
            if self._L == 0:
                self._L = len(_df)
                self._index = pd.to_datetime(_df['time'])

            self._stock_df[stock] = _df[self._indicators]
        self._data = self.compress_data()


        # pre calcualte the price at every iteration for efficiency
        self._prices = np.array([{stock: self._data[i, 1 + s*5]
                                for s, stock in enumerate(stocks)} for i in range(self._L)])

        self.sis = {s: dict() for s in stocks}
        self.sinames = [(stock, indicator, i) for i, (stock, indicator) in enumerate(
                        product(self.sis, self._indicators))]

    @property
    def prices(self):
        siss = []
        if not self._verbose:
            print('> Precompiling data')
        for index in (tqdm(range(len(self)), total=len(self), desc = '> Precompiling data') if self._verbose else range(len(self))):
            A = {stock: dict() for stock in self.sis}
            for stock, indicator, i in self.sinames:
                A[stock][indicator] = self._data[:index, i]
            siss.append(A)
        return self._prices, siss

    def get(self, index):

        for stock, indicator, i in self.sinames:
            self.sis[stock][indicator] = self._data[:index, i]
        
        return self.sis

    def len(self):
        return self._L
    
    def __len__(self):
        return self._L

    @property
    def index(self):
        return self._index

    def compress_data(self):

        return np.concatenate(
            [df.loc[:, df.columns != 'time'].to_numpy() for df in self._stock_df.values()], axis=1).astype('float64')
