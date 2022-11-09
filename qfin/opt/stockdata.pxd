cimport numpy as np

cdef class StockData:
    cdef list _indicators
    cdef int _i 
    cdef dict _stock_df
    cdef int _L 
    cdef np.float64_t[:, :] _data 
    cdef dict[:] _prices 

