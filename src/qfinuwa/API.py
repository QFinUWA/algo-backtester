import os
import pandas as pd
import urllib.parse as urlparse
from itertools import product
from multiprocessing.pool import ThreadPool
from multiprocessing import cpu_count
import time
from IPython import get_ipython

try:
    shell = get_ipython().__class__.__name__
    if shell in ['ZMQInteractiveShell']:
        from tqdm import tqdm_notebook as tqdm   # Jupyter notebook or qtconsole or Terminal running IPython  
    else:
         from tqdm import tqdm   
except NameError:
    from tqdm import tqdm      # Probably standard Python interpreter

'''
NOTE:  The data is derived from the Securities Information Processor (SIP) market-aggregated data.
'''
class API:

    def __init__(self, api_key_path='API_key.txt', data_folder=None):

        self.data_folder = data_folder

        if not os.path.exists(data_folder):
            os.mkdir(data_folder)

        if not os.path.exists(api_key_path):
            raise ValueError(f'{api_key_path} does not exist.')

        with open(api_key_path, 'r') as f:
            self.apikey = f.readline()

    def get_params(self, stock, year, month):

        params = {
            'function': 'TIME_SERIES_INTRADAY_EXTENDED',
            'symbol': stock,
            'interval': '1min',
            'datatype': 'csv',
            'adjusted': 'true',
            "slice": f'year{year}month{month}',
            'apikey': self.apikey
        }
        # print(
        #     f'https://www.alphavantage.co/query?{urlparse.urlencode(params)}')
        return f'https://www.alphavantage.co/query?{urlparse.urlencode(params)}'

    def to_path(self, stock):
        return os.path.join(self.data_folder, f"{stock}.csv")

    def is_cached(self, stock):

        # file = self.to_path(stock, *date_index)

        # if os.path.exists(file):
        #     return True

        # folder = self.to_path(stock, *date_index, exclude_file=True)
        # if not os.path.exists(folder):
        #     os.makedirs(folder, exist_ok=True)

        return os.path.exists(self.to_path(stock))

    def process_request(self, url_request):
        # print(f'processed {url}')
        df = pd.read_csv(url_request)

        assert len(df) > 0, f'{df}'
        # if not df:
        #     return (stock, None)
        # df = df.drop(columns=['open', 'high', 'low'])
        return df

    def allign_data(self, dfs):

        if len(dfs)==0:
            return

        # go through all stocks and find last start date
        start_date = max([pd.to_datetime(df.index.min()) for _, df in dfs])
        # first end date
        end_date = min([pd.to_datetime(df.index.max()) for __, df in dfs])
        # crop dataframes
        with tqdm(dfs) as pbar:
            for filepath, df in dfs:          
                pbar.set_description(f'> Alligning {filepath}')
                cropped_df = df.loc[(df.index >= start_date) & (df.index <= end_date)]

                # fill out with averages
                filled_df = cropped_df.resample('T').mean().interpolate(method='time')

                # remove any times not in interval (4:00 - 20:00]
                interval_df = filled_df.loc[(filled_df.index.hour >= 4) & (filled_df.index.hour < 20)]
                interval_df = interval_df.loc[(interval_df.index.dayofweek != 5) & (interval_df.index.dayofweek != 6)]

                interval_df.to_csv(filepath)

                # TODO - download new data
                pbar.update(1)
                pbar.set_description(f'> Done Alligning')  # hacky way to set last description but hey it works

    def fetch_data(self, stocks):

        if isinstance(stocks, str):
            stocks = [stocks]
        
        stocks.insert(0, 'SPY')

        stock_df = []

        years = [2,1]
        months = range(12,0,-1)
        with tqdm(stocks) as pbar:
            for stock in pbar:

                urls = [self.get_params(stock, year, month)
                        for year, month in product(years, months)][:-3]

                n_threads = min(cpu_count(), len(urls))

                pbar.set_description(f'> Fetching {stock} ({n_threads} threads)')

                if not self.is_cached(stock):

                    with ThreadPool(n_threads) as p:
                        results = p.map(self.process_request, urls)
                    # pbar.set_description(f'> Processing {stock}')
                    df = pd.concat(results, axis=0, ignore_index=True)
                    df['time'] = pd.to_datetime(df['time'])
                    df = df.set_index('time')
                    df.sort_values(
                        by='time', inplace=True)
                    
                    
                    # df.to_csv(self.to_path(stock), index=False)
                    # df = df.drop(columns=['open', 'high', 'low']).rename(
                    #     columns={"close": "price"})
                    # df = df[24*60:-24*60]
                    pbar.set_description(f'> Saving {stock} ({len(df)} rows)')
                    # df.to_csv(self.to_path(stock + '_raw'), index=False)
                    stock_df.append((self.to_path(stock), df))

                pbar.update(1)
                pbar.set_description(f'> Done Fetching') # hacky way to set last description but hey it works
        self.allign_data(stock_df)

