"""Typed public response contracts for Pangram detection results."""

from typing import TypedDict

__all__ = [
    "BulkResultItem",
    "BulkResultMetadata",
    "BulkResults",
    "BulkResultsPage",
    "PredictionResult",
    "PredictionWindow",
]


class _PredictionWindowRequired(TypedDict):
    text: str
    label: str
    ai_assistance_score: float
    confidence: str
    start_index: int
    end_index: int
    word_count: int
    token_length: int


class PredictionWindow(_PredictionWindowRequired, total=False):
    """A classified text window.

    ``is_humanized`` and ``humanizer_score`` are present on Pangram 4
    responses and omitted from classic-model responses.
    ``edit_bucket_probabilities`` is a separately feature-gated vector of 15
    probabilities.
    """

    is_humanized: bool
    humanizer_score: float
    edit_bucket_probabilities: list[float]


class _PredictionResultRequired(TypedDict):
    stage: str
    text: str
    version: str
    headline: str
    prediction: str
    prediction_short: str
    fraction_ai: float
    fraction_ai_assisted: float
    fraction_human: float
    num_ai_segments: int
    num_ai_assisted_segments: int
    num_human_segments: int
    windows: list[PredictionWindow]


class PredictionResult(_PredictionResultRequired, total=False):
    """A successful asynchronous Pangram detection result."""

    dashboard_link: str


class BulkResultMetadata(TypedDict):
    """Status metadata shared by successful and failed bulk items."""

    index: int
    id: str | None
    task_id: str | None
    stage: str
    error: str | None


class BulkResultItem(BulkResultMetadata):
    """A bulk item and its prediction once processing succeeds."""

    result: PredictionResult | None


class BulkResultsPage(TypedDict):
    """One response page from the Bulk API results endpoint."""

    bulk_id: str
    offset: int
    limit: int
    total_items: int
    items: list[BulkResultItem]
    failed_items: list[BulkResultMetadata]


class BulkResults(TypedDict):
    """All result pages aggregated by the SDK."""

    bulk_id: str
    total_items: int
    items: list[BulkResultItem]
    failed_items: list[BulkResultMetadata]
