#%%
from setuptools import setup, find_packages
# %%
NAME = "AInCT"
VERSION = "0.0.1"
DESCR = "Python code for HyperCT incluing: reconstruction, evaluation and angle propose"
#REQUIRES = ['numpy', 'scipy', 'scikit-learn', 'svmbir', 'scikit-image', 'fitsio', 'tifffile', 'matplotlib', 'pandas', 'gmcluster']
#LICENSE = "BSD-3-Clause"
PACKAGE_DIR = "AInCT"

setup(name=NAME,
      version=VERSION,
      description=DESCR,
      packages=find_packages(),
      )