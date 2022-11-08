# QFIN's Algorithmic Backtester (QFAB)

## Setup

To set up, run the following command at the root of the codebase:

``python setup.py build_ext --inplace``

This will compile the cython shared objects that provide functionality. 

Currently, I am working on automatiting this via conda forge or PyPI. 

The final goal is to simply run either:

- conda install qfin
- pip install qfin

## Running 

An example script is provided (``frontend_plan.py``) which is currently being used to model the design of the framework.

The design of the framework is to provide a base ``Algorithm`` class that contains 

- the functions used to add indicators
- the logic function for trading
- any variables required for the above

The implemented algoirthm (instanciated via ``class MyAlgorithm(qfin.Algorithm)``), will take a Portfolio object that contains the cash, holdings and history of trades and use incoming and past information (in the form of a dictionary of arrays of data).

The ``Backtester`` class will handle all of this and return results. 