import setuptools


setuptools.setup(name='qfinuwa',
      description='Framework for backtesting quantitative trading algorithims.',
      package_dir = {"": "src"},
      packages = setuptools.find_packages(where="src"),
      python_requires = ">=3.6",
      install_requires=[
          'tqdm', 'tabulate', 'bokeh', 'requests', 
      ]
      )
