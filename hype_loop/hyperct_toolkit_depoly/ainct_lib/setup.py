"""Packaging configuration for AInCT."""

from pathlib import Path
import re

from setuptools import find_packages, setup

ROOT_DIR = Path(__file__).parent
PACKAGE_NAME = "AInCT"


def read_version() -> str:
      """Extract the package version without importing the package."""
      init_file = ROOT_DIR / PACKAGE_NAME / "__init__.py"
      version_match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", init_file.read_text())
      return version_match.group(1) if version_match else "0.0.0"


def read_readme() -> str:
      readme_file = ROOT_DIR / "README.md"
      return readme_file.read_text(encoding="utf-8")


setup(
      name=PACKAGE_NAME,
      version=read_version(),
      description=(
            "Python code for the HyperCT AI loop including reconstruction, evaluation, and angle proposal"
      ),
      long_description=read_readme(),
      long_description_content_type="text/markdown",
      url="https://github.com/ornlneutronimaging/AInCT",
      license="BSD-3-Clause",
      packages=find_packages(exclude=("__old_version", "build", "AInCT.egg-info")),
      python_requires=">=3.8",
      install_requires=[
            "numpy",
            "pandas",
            "dxchange",
            "h5py",
            "svmbir",
            "scikit-image",
            "requests",
            "requests-oauthlib",
            "oauthlib",
            "cryptography",
            "urllib3",
      ],
      include_package_data=True,
      classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: BSD License",
            "Operating System :: OS Independent",
      ],
)