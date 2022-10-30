
from tqdm import tqdm
class Algorithm:

    def __init__(self):
        self._stocks = None
        self._fee = 0

    def load_stocks(self, stocks):
        self._stocks = stocks

    def add_fee(self, fee):
        self._fee = fee

    # to override
    def on_data(self, data):
        pass

    def backtest(self, stock_data, sample_period='3 months', overlap=True, samples=20, fee=0.01):

        I = iter(stock_data)
        for t in tqdm(I):
            # print({k: len(v) for k,v in t.items()})
            self.on_data(t)
        