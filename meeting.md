# QFAB - Exec Summary (07.01.23)

## The overall goals of the project are to 
- Formalise hyperparamters
- Clean up the "Preprocessed" data section
- Reduce global variables
- Abract away csv management
- Make sharing code easier (works on other machines)
- easy to set up the framework (pip install)
- Add automated testing for parameter sweeps

## Downloading stockdata
- use multithreading to download stocks faster
- reduce options to download data
    - API only supports 2 years history, so by default all 2 years of 1 min data is downloaded into a specified folder 
    - API has some missing datapoints (unpredictably) so the platform fills them in 
    - platform ensures all data is in the same time window
    - Progress Bars + Caching

## Passing stockdata into platform
- Creates optimal datastructure for fast splicing and indexing
- Big numpy array of values passed into 2D dictionary
  
    ```py
    data = {     
            "AAPL": {
                "price": [1220, 1219, 1232, ...],
                "volume": [1020, 991, 1456, ...]
                "custom_indicator": [1.211, 0.911, 0.011, ...],
                ...
            },
            "GOOG": {
                "price": [977, 988, 999, ...],
                "volume": [230, 521, 190],
                "custom_indicator": [1.001, 0.991, 0.433, ...],
                ...
            },
            ...
    }
    ```


    Still need to design system to update this datastructure when new indicators are added
    
    Old platform with 1 stock, 5 cols
    - 12.8k it/sec => 31.6 secs (1x)

    New platform with 1 stock, 5 cols
    - 287k it/sec => 2.00 secs (22.5x)
    
        Note: New platform only needs 2 cols as a base (removed open, high, low)

    New platform with 1 stock, 2 cols (price (close), volume)
    - 532k it/sec => 1.00 sec (41.6x)
  
## Cython

Some of the performance benefit can be attributed to using Cython, but this makes development and deployment complicated.
- No Cython = Pip (Easy)
- Cython = conda (hard)
- TODO: experiment by removing Cython at the end of development


## Automated Testing

Still a WIP - however the design suits this feature


## Plotting

Plan is to use the same library as the old framework with added features.



    
