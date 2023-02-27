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

    def __init__(self, data_path: str, stocks: list = None, verbose: bool=False):

        self._indicators = ['open', 'close', 'high', 'low', 'volume']
        self._i = 0

        self._stock_df = dict()

        self._L = 0
        self._index = None

        self._verbose = verbose

        self.spy = None

        if stocks is None:
            stocks = [os.listdir(data_path)[0].split('.')[0]]

        if len(stocks) == 0:
            raise ValueError('No stocks provided')

        for stock in (tqdm(stocks + ['SPY'], desc='> Fetching data') if verbose else stocks):

            _df = pd.read_csv(os.path.join(data_path, f'{stock}.csv'))
            
            if self._L == 0:
                self._L = len(_df)
                self._index = pd.to_datetime(_df['time'])

            if stock == 'SPY':
                self.spy = _df['close'].to_numpy()
                continue

            self._stock_df[stock] = _df[self._indicators]
        self._data = self.compress_data()

        self._stocks = sorted(stocks)

        # pre calcualte the price at every iteration for efficiency
        self._prices = np.array([{stock: self._data[i, 1 + s*5]
                                for s, stock in enumerate(stocks)} for i in range(self._L)])

        # self.sis = {s: dict() for s in stocks}
        self.sinames = [(indicator, stock , i) for indicator, (i, stock) in 
                        product(self._indicators, enumerate(self._stocks))]
        

    @property
    def stocks(self):
        return self._stocks

    @property
    def prices(self):
        siss = []
        for index in (tqdm(range(len(self)),  desc = '> Precompiling data', mininterval=0.5) if self._verbose else range(len(self))):
            A = {indicator: dict() for indicator in self._indicators}
            
            for indicator, stock, i in self.sinames:
                A[indicator][stock] = self._data[:index+1, i]
            siss.append(A)


        return self._prices, siss
    
    def __len__(self):
        return self._L

    @property
    def index(self):
        return self._index

    def compress_data(self):

        return np.concatenate(
            [df.loc[:, df.columns != 'time'].to_numpy() for df in sorted(self._stock_df.values())], axis=1).astype('float64')
