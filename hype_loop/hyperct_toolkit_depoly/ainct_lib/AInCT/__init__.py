"""Public package interface for AInCT."""

__version__ = "0.0.3"

import warnings
warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API",
    category=UserWarning,
)
import dxchange

# Primary public classes
from .data_handler import DataHandler
#from .Evaluator import CNNEVA

# Convenience module re-exports (keep explicit to avoid wildcard leakage)
from . import utils, preprocessing_utils, EA2S, EICClient

# Note: Calibrator was removed in the clean_version branch and archived to __old_version/
__all__ = [
	"__version__",
	"DataHandler",
	"CNNEVA",
	"utils",
	"preprocessing_utils",
	"EA2S",
	"EICClient",
]
