import setuptools


setuptools.setup(name='qfinuwa',
      version='1.0.0',
      description='Framework for backtesting quantitative trading algorithims.',
      package_dir = {"": "src"},
      packages = setuptools.find_packages(where="src"),
      python_requires = ">=3.6"
      )
