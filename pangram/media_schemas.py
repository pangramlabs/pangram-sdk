"""Typed image and video API responses; runtime values are dictionaries."""

from typing import Literal, TypedDict


class MediaTaskSubmission(TypedDict):
    task_id: str


class MediaError(TypedDict):
    error: str
    error_code: str
    retryable: bool


class _MediaTaskFailureRequired(TypedDict):
    task_id: str
    stage: Literal["STAGE_FAILED"]
    error: MediaError


class MediaTaskFailure(_MediaTaskFailureRequired, total=False):
    frames_processed: int
    total_frames: int


class ImageHeatmap(TypedDict):
    grid: list[list[float]]
    patch_stride: int


class MediaThumbnail(TypedDict):
    data_url: str
    width: int
    height: int


class ImageMetadata(TypedDict, total=False):
    c2pa: dict[str, object]
    software: list[dict[str, object]]
    camera: dict[str, object] | None


class ImageResult(TypedDict):
    """Completed image analysis, including nullable provenance-only fields."""

    task_id: str
    stage: Literal["STAGE_SUCCESS"]
    prediction: Literal[
        "AI Detected", "Likely AI", "Unsure", "Likely No AI", "No AI", "Partially AI"
    ]
    ai_likelihood: float | None
    confidence: Literal["Low", "Medium", "High"] | None
    detection_source: Literal["model", "c2pa"]
    version: str | None
    heatmap: ImageHeatmap | None
    metadata: ImageMetadata
    thumbnail: MediaThumbnail | None


class ImageProcessingStatus(TypedDict):
    task_id: str
    stage: Literal["STAGE_IMAGE_INFERENCE", "STAGE_IMAGE_FINALIZING"]


ImageTaskStatus = ImageProcessingStatus | ImageResult | MediaTaskFailure


class _VideoSourceRequired(TypedDict):
    file_name: str
    content_type: str
    size_bytes: int
    duration_ms: int
    width: int
    height: int


class VideoSource(_VideoSourceRequired, total=False):
    fps: float | None


class _VideoFrameResultRequired(TypedDict):
    prediction: Literal["AI Detected", "Human", "Mixed", "Unsure"]
    detection_source: Literal["model"]
    version: str
    heatmap: ImageHeatmap
    metadata: ImageMetadata
    thumbnail: MediaThumbnail


class VideoFrameResult(_VideoFrameResultRequired, total=False):
    stage: Literal["STAGE_SUCCESS"]
    ai_likelihood: float | None
    confidence: Literal["Low", "Medium", "High"] | None


class _VideoFrameRequired(TypedDict):
    frame_id: str
    timestamp_ms: int
    result: VideoFrameResult


class VideoFrame(_VideoFrameRequired, total=False):
    smoothed_label: str
    shot_change: bool


class VideoTimeRange(TypedDict):
    start_ms: int
    end_ms: int


class _VideoSegmentRequired(TypedDict):
    id: str
    range: VideoTimeRange
    prediction_short: Literal[
        "human", "likely_human", "unsure", "likely_ai", "ai", "mixed"
    ]
    prediction: str
    frame_ids: list[str]


class VideoSegment(_VideoSegmentRequired, total=False):
    confidence: Literal["Low", "Medium", "High"] | None


class VideoSampling(TypedDict):
    fps: float


class _VideoResultRequired(TypedDict):
    task_id: str
    stage: Literal["STAGE_SUCCESS"]
    schema_version: Literal["1.1"]
    created_at: str
    prediction_short: Literal["no_ai", "mixed", "ai", "unsure"]
    headline: Literal["No AI detected", "AI Detected", "Unsure"]
    prediction: str
    detection_source: Literal["model", "c2pa"]
    version: str | None
    source: VideoSource
    metadata: ImageMetadata
    sampling: VideoSampling | None
    frames: list[VideoFrame]
    segments: list[VideoSegment]
    fraction_ai: float
    fraction_human: float
    fraction_mixed: float
    frames_processed: int
    total_frames: int


class VideoResult(_VideoResultRequired, total=False):
    """Completed video analysis in the public 1.1 response format."""

    confidence: Literal["Low", "Medium", "High"] | None
    fraction_unsure: float
    fraction_likely_ai: float
    fraction_likely_human: float
    detailed_labels: bool
    smoothing: dict[str, object]
    ai_segment_gate: dict[str, object]
    mixed_display: dict[str, object]


class _VideoProcessingRequired(TypedDict):
    task_id: str
    stage: Literal[
        "STAGE_VIDEO_EXTRACTION", "STAGE_VIDEO_INFERENCE", "STAGE_VIDEO_FINALIZING"
    ]


class VideoProcessingStatus(_VideoProcessingRequired, total=False):
    frames_processed: int
    total_frames: int


VideoTaskStatus = VideoProcessingStatus | VideoResult | MediaTaskFailure
