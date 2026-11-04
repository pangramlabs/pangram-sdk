"""Define the public objects available from ``import pangram``."""

__version__ = "1.1.0"
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
from pangram.media import MediaRequestError, MediaTaskError, MediaTaskTimeout
from pangram.media_schemas import (
    MediaError,
    MediaTaskFailure,
    ImageResult,
    ImageTaskStatus,
    MediaTaskSubmission,
    VideoFrame,
    VideoResult,
    VideoSegment,
    VideoSource,
    VideoTaskStatus,
)

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
    "ImageResult",
    "ImageTaskStatus",
    "MediaTaskSubmission",
    "MediaError",
    "MediaTaskFailure",
    "VideoFrame",
    "VideoResult",
    "VideoSegment",
    "VideoSource",
    "VideoTaskStatus",
    "MediaRequestError",
    "MediaTaskError",
    "MediaTaskTimeout",
]
