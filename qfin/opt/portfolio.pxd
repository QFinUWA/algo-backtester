
cimport numpy as np

cdef class Portfolio:
    cdef dict _curr_prices
    cdef int _i 
    cdef float _cash 
    cdef float _fee_mult
    cdef list _stocks 
    cdef dict _stock_to_id
    cdef dict _stock_id 
    cdef dict _curr_longs 
    cdef dict _curr_shorts 
    cdef np.float64_t[:, :] _history


    cpdef public buy(Portfolio self , str stock, float quantity, float value)
    cpdef public sell(Portfolio self  , str stock, float quantity, float value)
    cpdef public buy_all(Portfolio self, str stock)
    cpdef public sell_all(Portfolio self, str stock)
    cpdef _add_to_history(Portfolio self, str stock, int sell, float amount)