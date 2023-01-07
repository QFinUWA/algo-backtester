from opt.stockdata import StockData
from libcpp cimport bool
from cyalgorithm cimport CythonAlgorithm

cdef class CythonBacktester:
    cdef object _data 
    cdef list _stocks 
    cdef list _update_indicators
    cdef float _cash
    cdef float _fee
    cdef dict _algorithm_params
    cdef dict _indicator_params
    cdef type strategy
