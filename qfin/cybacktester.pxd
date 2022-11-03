cimport numpy as np
from opt.stockdata cimport StockData
from libcpp cimport bool
from cyalgorithm cimport CythonAlgorithm

cdef class CythonBacktester:
    cdef StockData _data 
    cdef list _stocks 
    cdef list _update_indicators