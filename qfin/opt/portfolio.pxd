
cimport numpy as np

cdef class Portfolio:
    cdef dict _curr_prices
    cdef int _i 
    cdef float _cash 
    cdef float _fee 
    cdef list _stocks 
    cdef dict _stock_id 
    cdef dict _curr_longs 
    cdef dict _curr_shorts 
    cdef np.float64_t[:, :] _history

    cpdef public enter_position(Portfolio self, str long, str stock, float quantity, float value)