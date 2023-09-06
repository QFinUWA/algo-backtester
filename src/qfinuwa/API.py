import os
import pandas as pd
import urllib.parse as urlparse
from itertools import product
from multiprocessing.pool import ThreadPool
from multiprocessing import cpu_count
import requests
import zipfile
from functools import reduce
import io
from typing import Union
import time
from datetime import datetime

# from IPython import get_ipython
# try:
#     shell = get_ipython().__class__.__name__
#     if shell in ['ZMQInteractiveShell']:
#         from tqdm.notebook import tqdm as tqdm   # Jupyter notebook or qtconsole or Terminal running IPython  
#     else:
#          from tqdm import tqdm   
# except NameError:
#     from tqdm import tqdm      # Probably standard Python interpreter
from tqdm import tqdm 

'''
NOTE:  The data is derived from the Securities Information Processor (SIP) market-aggregated data.
'''
class API:

    #---------------[Public Methods]-----------------#    
    @classmethod
    def from_google_drive(cls, file_ids: str, data_folder: str) -> None:
        '''
        Fetches data from a google drive provided by QFIN. The data is stored in the folder specified by `data_folder`.

        ### Parameters
        - ``file_ids`` (``str``): The path to a file containing the file ids of the data.
        - ``data_folder`` (``str``): The path to the folder where the data will be stored.

        ### Returns
        ``None``
        '''
        if not os.path.exists(data_folder):
            os.mkdir(data_folder)

        if file_ids is not None:
            with open(file_ids, 'r') as f:
                file_ids = [k.strip('\n') for k in f.readlines()]

        with ThreadPool() as p:
            p.starmap(cls._download_file_from_google_drive, [(fileid, data_folder) for fileid in file_ids])
    

    @classmethod
    def fetch_stocks(cls, stocks: Union[str,  list], api_key_path: str, data_folder: str, download_raw: bool = False, months: int = 60) -> None:
        '''
        Fetches the data from the SIP market-aggregated data. The data is provided by the SEC. An API key is required. The data is stored in the folder specified by `data_folder`.

        ### Parameters
        - ``stocks`` (``str``): The ticker(s) of the stock(s) to be downloaded. If multiple stocks are required, a list of tickers can be provided.
        - ``api_key_path`` (``str``): The path to the file containing the API key.
        - ``download_raw`` (``bool``): If ``true``, downloads the data straight from the API provider, without alligning.
        ### Returns
        ``None``
        '''
    
        if not os.path.exists(api_key_path):
            raise ValueError(f'{api_key_path} does not exist.')

        with open(api_key_path, 'r') as f:
            apikey = f.readline()

        if not os.path.exists(data_folder):
            os.mkdir(data_folder)

        if isinstance(stocks, str):
            stocks = [stocks]
        
        # stocks.insert(0, 'SPY')

        stock_df = []

        today = pd.to_datetime('today').strftime("%d/%m/%Y")
        last = (pd.to_datetime(today) - pd.DateOffset(months=months+1))
        month_periods = pd.date_range(start=last, end=today, freq='M').strftime("%Y-%m")
        month_periods = [k.split('-') for k in month_periods[:-1]]
        
        
        with tqdm(stocks) as pbar:
            for stock in stocks:

                urls = [cls._get_params(stock, year, month, apikey)
                        for year, month in month_periods]

                n_threads = min(cpu_count(), len(urls))

                pbar.set_description(f'> Fetching {stock} ({n_threads} threads)')

                path = os.path.join(data_folder, f"{stock}.csv")
                t_last = time.time()
                if not os.path.exists(path):
                    with ThreadPool(n_threads) as p:
                        results = p.map(cls._process_request, urls)
                    # pbar.set_description(f'> Processing {stock}')
                    if any(map(lambda df: len(df) ==0, results)):
                        # raise RuntimeError('Empty dataframe...')
                        print('Empty dataframe... skipping')
                        continue
                    # print(results[0].head(5))
                    df = pd.concat(results, axis=0, ignore_index=True)
                    # df.to_csv(stock + '_raw.csv', index=True)
                    try:
                        print(df.columns)
                        df.rename(columns={'timestamp': 'time'}, inplace=True)
                        df['time'] = pd.to_datetime(df['time'])
                    except:
                        print(f'{stock} - Error parsing timestamp')
                        df.to_csv(f'data/error_{stock}.csv')
                        continue
                    df = df.set_index('time')
                    df.sort_values(
                        by='time', inplace=True)
                    
                    # print(df.head())
                    
                    pbar.set_description(f'> Saving {stock} ({len(df)} rows)')
                    # df.to_csv('raw/' + stock + '_raw.csv', index=True)
                    path = os.path.join(data_folder, f"{stock}.csv")
                    stock_df.append((path, df))
                    if download_raw:
                        df.to_csv(path)
                
                t_now = time.time()
                # time.sleep( max(0, 60 - (t_now-t_last)))
                pbar.set_description('Blocking...')
                
                pbar.update(1)
                pbar.set_description(f'> Done Fetching') # hacky way to set last description but hey it works
        

        if not download_raw:
            cls._allign_data(stock_df)

    #---------------[Private Methods]-----------------# 
    # @classmethod
    # def _download_file_from_google_drive(cls, id: str, data_folder: str) -> None:
    #     URL = "https://docs.google.com/uc?export=download"
    #     # URL = 'https://drive.google.com/drive/folders/?usp=share_link'

    #     session = requests.Session()

    #     response = session.get(URL, params = { 'id' : id }, stream = True)

    #     def get_confirm_token(response):
    #         for key, value in response.cookies.items():
    #             if key.startswith('download_warning'):
    #                 return value

    #         return None
        
    #     token = get_confirm_token(response)

    #     token = None
    #     for key, value in response.cookies.items():
    #         if key.startswith('download_warning'):
    #             token = value
    #             break

    #     if token:
    #         params = { 'id' : id, 'confirm' : token }
    #         response = session.get(URL, params = params, stream = True)
        
    #     CHUNK_SIZE = 32768
    #     try:
    #         with io.BytesIO() as f:
    #             for chunk in response.iter_content(CHUNK_SIZE):
    #                 if chunk: # filter out keep-alive new chunks
    #                     f.write(chunk)
                
    #             # with zipfile.ZipFile(f) as z:
    #             #     z.extractall(path=data_folder)
    #     except:
    #         print(f'Error downloading file {id} - skipping')


    @classmethod
    def _get_params(cls, stock: str, year: int, month: int, api_key: str) -> str:

        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': stock,
            'interval': '1min',
            'datatype': 'csv',
            'adjusted': 'true',
            'month': f'{year}-{month}',
            'outputsize': 'full',
            'apikey': api_key,
        }
        # print(
        #     f'https://www.alphavantage.co/query?{urlparse.urlencode(params)}')
        return f'https://www.alphavantage.co/query?{urlparse.urlencode(params)}'


    @classmethod
    def _process_request(cls, url_request: str) -> pd.DataFrame:
        # print(f'processed {url}')
        df = pd.read_csv(url_request)

        # assert len(df) > 0, f'{df}'
        # if not df:
        #     return (stock, None)
        # df = df.drop(columns=['open', 'high', 'low'])
        return df

    @classmethod
    def _allign_data(cls, dfs: list) -> None:

        if len(dfs)==0:
            return

        # go through all stocks and find last start date
        start_date = [df.index.min() for _, df in dfs]
        # first end date
        end_date = [df.index.max() for __, df in dfs]
        # crop dataframes
        start_date, end_date = max(start_date),  min(end_date)

        with tqdm(dfs) as pbar:

            new_index = reduce(lambda a,b: a.union(b), (df.index for _, df in dfs))

            new_index = new_index[(new_index >= start_date) & (new_index <= end_date)]
            new_index = new_index[(new_index.hour + new_index.minute/60 >= 9.5)  & (new_index.hour < 16)]

            for filepath, df in dfs:          
                pbar.set_description(f'> Alligning {filepath}')

                # fill out with averages
                # filled_df = df.resample('T').mean().interpolate(method='time')
                # cropped_df = filled_df.loc[(filled_df.index >= start_date) & (filled_df.index <= end_date)]

                # remove any times not in interval (4:00 - 20:00]
                # interval_df = cropped_df.loc[(cropped_df.index.hour >= 4) & (cropped_df.index.hour < 20)]
                # interval_df = interval_df.loc[(interval_df.index.dayofweek != 5) & (interval_df.index.dayofweek != 6)]
                # print(df.columns)
                # print(new_index)
                new_df = df.reindex(new_index, axis=0).interpolate(method='linear')
                # convert to 3dps
                new_df = new_df.round(3)
                # round volume
                new_df['volume'] = new_df['volume'].round(0)

                new_df.to_csv(filepath)

                # TODO - download new data
                pbar.update(1)
                pbar.set_description(f'> Done Alligning')  # hacky way to set last description but hey it works
        
        return

