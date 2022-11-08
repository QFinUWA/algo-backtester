from cybacktester cimport CythonBacktester
from cyalgorithm cimport CythonAlgorithm

class Backtester(CythonBacktester):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Algorithm(CythonAlgorithm):

    def __init__(self):
        super().__init__()
