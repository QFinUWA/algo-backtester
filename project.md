# Plan

1. Anonymous stocks
2. small sample of stocks
3. pairs trading?
4. second data?
5. usb data?


So a couple things about the trading team project:

1) The test set will be the last 3 months, and will be withheld from the teams.
1) It would be a good idea to reduce the scope to a handful of stocks (runs faster, more fair to assess, easier to generalise strategy)
2) These stocks would have randomized names (so finance bros won't have an edge by predicting the test set)
3) Even though I made a pog API data puller there's no way, without using an encrytion server, that we could prevent teams from seeing which names have been changed by inspecting the code. It would be smarter to have the students download from a google drive (I could even implement this into the API class pretty easily, eg "API.download('C:\\data_folder\\))")
4) We can distribute this data before the project, either all at once or piece by piece, so the traders can do data exploration (by themselves before they're put into teams, or in their teams)

Add ``on_finish`` function.

My Approach

Consider a single stock. We can decide a list of indicators used to make decisions about weather to buy/sell that stock.

If we have an arbitary function ``f(...)`` that takes in the list of indicators at timestep ``i`` and outputs a value between -1 and 1. Axiomatically we decide that 0.5 == buy and -0.5 == sell. 

We implement a linear weighted sum of the indicators, giving us a single parameter for each indicator. 

We can retrospectively analyse the best time to buy and sell the stock from time ``i`` onwards. Either:
- after each timestep, update the weights of ``f``
- after each test, update the weights of ``f``.

The update rule will be 

w_i = w_i + lr*(f(data)-EXP)*w_i

May need to include rules like, don't trade for 1 day after buying/selling