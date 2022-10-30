
from tqdm import tqdm


class Algorithm:

    def __init__(self):
        self._stocks = None
        self._fee = 0

    # goofy ah name TODO change this
    '''
    Why is this not part of the constructor? Because this
    implementation is designed to be intuitive, and it may
    confuse users if the constructor had these parameters
    '''

    def assimilate_backtester(self, fee: float, stocks: list):
        self._fee = fee
        self._stocks = stocks

    # to override
    def on_data(self, data: dict):
        pass
