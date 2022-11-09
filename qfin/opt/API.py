import os
import pandas as pd
import urllib.parse as urlparse
from itertools import product
from tqdm import tqdm
from multiprocessing.pool import Pool
from multiprocessing import cpu_count


class API:

    def __init__(self, api_key_path):

        if not os.path.exists(api_key_path):
            raise ValueError(f'{api_key_path} not a valid path')

        with open(api_key_path, 'r') as f:
            self.apikey = f.readline()

    def get_params(self, stock, date):
        year, month = date

        params = {
            'function': 'TIME_SERIES_INTRADAY_EXTENDED',
            'symbol': stock,
            'interval': '1min',
            'outputsize': 'full',
            'datatype': 'csv',
            'adjusted': 'true',
            "slice": f'year{year}month{month}',
            'apikey': self.apikey
        }

        return f'https://www.alphavantage.co/query?{urlparse.urlencode(params)}'

    def fetch_data(self, stocks, start, end):
        start_year, start_month = start
        end_year, end_month = end

        s = 12*start_year + start_month-1
        e = 12*end_year + end_month-1

        dates = [(i//12, i % 12+1) for i in range(s, e+1)]

        urls = [self.get_params(stock, date)
                for stock, date in product([stocks], dates)]

        with Pool(cpu_count()) as p:
            results = p.map(pd.read_csv, urls)
            # print([type(a) for a in results])
        # print(urls)
        # return
        # for url in tqdm(urls):
        #     df = pd.read_csv(url, parse_dates=[0])
        #     df.rename({'time': 'date'}, inplace=True, axis=1)
        #     # TODO: drop cols


if __name__ == '__main__':
    A = API(r'C:\Users\isaac\git\algo-backtester\API_key.txt')

    A.fetch_data('GOOG', (1, 1), (2, 12))
