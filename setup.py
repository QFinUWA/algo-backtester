from setuptools import setup, Extension, find_packages
from Cython.Build import cythonize
import numpy
from Cython.Compiler import Options

Options.always_allow_keywords = True
# import os

# ext_modules = [Extension("backtester", ["qfin/backtester.pyx"]),
#                Extension("portfolio", ["qfin/opt/portfolio.pyx"])]


# def find_pyx(path='.'):
#     pyx_files = []
#     for root, dirs, filenames in os.walk(path):
#         for fname in filenames:
#             if fname.endswith('.pyx'):
#                 pyx_files.append(os.path.join(root, fname))
#     return pyx_files


setup(name='qfin',
      version='0.0',
      description='Framework for backtesting quantitative trading algorithims.',
      packages=find_packages(),
      include_dirs=[numpy.get_include()],
      ext_modules=cythonize(["qfin/backtester.pyx",
                             "qfin/opt/stockdata.pyx",
                             "qfin/cyalgorithm.pyx",
                             "qfin/cybacktester.pyx",
                             "qfin/opt/portfolio.pyx"]
                            )
      )
