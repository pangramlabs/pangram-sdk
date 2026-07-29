"""Define the public objects available from ``import pangram``."""
__version__ = "0.4.0"
__author__ = "Max Spero"
__email__ = "max@pangram.com"
__license__ = "MIT"

from pangram.schemas import (
    BulkResultItem,
    BulkResultMetadata,
    BulkResults,
    BulkResultsPage,
    PredictionResult,
    PredictionWindow,
)
from pangram.text_classifier import PangramText

Pangram = PangramText

__all__ = [
    "Pangram",
    "PangramText",
    "BulkResultItem",
    "BulkResultMetadata",
    "BulkResults",
    "BulkResultsPage",
    "PredictionResult",
    "PredictionWindow",
]
