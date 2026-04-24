#%%
from setuptools import setup, find_packages
# %%
NAME = "CTQA"
VERSION = "0.0.1"
DESCR = "Python code for CNN based neutron CT reconstruction quality evaluation"
REQUIRES = ['torch', 'scikit-image', 'numpy', 'collections']
#LICENSE = "BSD-3-Clause"
PACKAGE_DIR = "CTQA"

setup(name=NAME,
      version=VERSION,
      description=DESCR,
      packages=find_packages(),
      )