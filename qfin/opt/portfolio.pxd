
cimport numpy as np

cdef class Portfolio:
    cdef dict _curr_prices
    cdef int _i 
    cdef float _cash 
    cdef float _fee_mult
    cdef float _fee_div
    cdef list _stocks 
    cdef dict _stock_to_id
    cdef float _short_value
    cdef dict _longs  
    cdef dict _shorts 
    cdef list _history_cols
    cdef np.float64_t[:, :] _history


    cpdef public enter_long(Portfolio self , str stock, int quantity)
    cpdef public sell_long(Portfolio self  , str stock, int quantity)
    cpdef public enter_short(Portfolio self, str stock, int quantity)
    cpdef public cover_short(Portfolio self, str stock, int quantity)
    cpdef _add_to_history(Portfolio self, str stock, int sell, float amount)