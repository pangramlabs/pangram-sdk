"""Native media methods shared by the Pangram and PangramText client names."""

import base64
import math
import time
from typing import Callable, cast
from uuid import UUID

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

from pangram._media_input import MediaInput, image_bytes, open_media, video_details
from pangram.media_schemas import (
    ImageResult,
    ImageTaskStatus,
    MediaTaskSubmission,
    VideoResult,
    VideoTaskStatus,
)

IMAGE_API_ENDPOINT = "https://image.external-api.pangram.com"
VIDEO_API_ENDPOINT = "https://video.external-api.pangram.com"
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class MediaRequestError(ValueError):
    """An HTTP, transport, or response-format error from a media API."""

    def __init__(
        self, message: str, *, status_code: int | None = None, retry_after: float = 0
    ):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class MediaTaskError(ValueError):
    """A terminal task failure; ``task_id`` and ``error`` preserve API details."""

    def __init__(self, task_id: str, error: dict[str, object]):
        self.task_id = task_id
        self.error = error
        super().__init__(f"Pangram media task {task_id} failed: {error}")


class MediaTaskTimeout(TimeoutError):
    """Polling expired. Resume the accepted task using ``task_id``."""

    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(
            f"Pangram media task {task_id} is still processing; resume polling this task ID"
        )


def _positive(value: float, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError(f"{name} must be a finite number greater than zero")
    return float(value)


def _task_id(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("task_id must be a valid UUID string") from exc


def _response(response: requests.Response, expected: int) -> dict[str, object]:
    try:
        delay = float(response.headers.get("Retry-After", "0"))
        delay = delay if math.isfinite(delay) and delay > 0 else 0
    except (ValueError, TypeError):
        delay = 0
    try:
        data = response.json()
    except ValueError as exc:
        raise MediaRequestError(
            "Media API returned a non-JSON response",
            status_code=response.status_code,
            retry_after=delay,
        ) from exc
    if response.status_code != expected:
        raise MediaRequestError(
            f"Media API returned HTTP {response.status_code}: {data}",
            status_code=response.status_code,
            retry_after=delay,
        )
    if not isinstance(data, dict):
        raise MediaRequestError(
            "Media API returned an invalid response object",
            status_code=response.status_code,
        )
    return data


class MediaMethods:
    """Media operations inherited by the public client. Use :class:`pangram.Pangram`."""

    api_key: str

    def _media_submit(
        self,
        url: str,
        timeout: float,
        *,
        headers: dict[str, str],
        json: dict[str, object] | None = None,
        data: MultipartEncoder | None = None,
    ) -> MediaTaskSubmission:
        try:
            response = requests.post(
                url,
                timeout=timeout,
                allow_redirects=False,
                headers=headers,
                json=json,
                data=data,
            )
        except requests.RequestException as exc:
            raise MediaRequestError(
                "Media submission failed before a response was received. It may have been accepted; "
                "the SDK has not retried the upload."
            ) from exc
        data = _response(response, 202)
        identifier = data.get("task_id")
        if not isinstance(identifier, str):
            raise MediaRequestError("Media submission response is missing task_id")
        try:
            _task_id(identifier)
        except ValueError as exc:
            raise MediaRequestError(
                "Media submission response has an invalid task_id"
            ) from exc
        return cast(MediaTaskSubmission, data)

    def submit_image(
        self, image: MediaInput, *, model: str, timeout: float = 60
    ) -> MediaTaskSubmission:
        """Submit an image path, bytes, or binary file and return its task ID.

        ``model`` is required: choose ``pangram-image-1``,
        ``pangram-image-flash-1``, or ``pangram-image-0.2``. ``default`` follows
        the server default (currently Image 0.2). Images are limited to 32 MiB.
        Submission is never automatically retried.
        """
        timeout = _positive(timeout, "timeout")
        if not isinstance(model, str) or not model.strip() or len(model.strip()) > 200:
            raise ValueError(
                "model must be a nonempty image model selector of at most 200 characters"
            )
        with open_media(image) as (file, _):
            encoded = base64.b64encode(image_bytes(file)).decode("ascii")
        return self._media_submit(
            f"{IMAGE_API_ENDPOINT}/v1/tasks",
            timeout,
            headers={"x-api-key": self.api_key},
            json={"image_b64": encoded, "model": model.strip()},
        )

    def submit_video(
        self,
        video: MediaInput,
        *,
        filename: str | None = None,
        timeout: float = 300,
    ) -> MediaTaskSubmission:
        """Stream an MP4, MOV, or WebM file and return its task ID.

        Accepts a path, bytes, or a seekable binary file. Supply ``filename``
        for bytes or an unnamed stream. The upload limit is 500 MiB. Processing
        uses server defaults. Borrowed streams remain open and are read from
        their current position. Submission is never automatically retried.
        """
        timeout = _positive(timeout, "timeout")
        with open_media(video) as (file, inferred):
            name, content_type = video_details(
                file, filename if filename is not None else inferred
            )
            body = MultipartEncoder(fields={"file": (name, file, content_type)})
            return self._media_submit(
                f"{VIDEO_API_ENDPOINT}/v1/video/tasks",
                timeout,
                headers={"x-api-key": self.api_key, "Content-Type": body.content_type},
                data=body,
            )

    def _media_status(
        self,
        base: str,
        path: str,
        task_id: str,
        timeout: float,
        *,
        params: dict[str, str] | None = None,
    ) -> dict[str, object]:
        identifier = _task_id(task_id)
        timeout = _positive(timeout, "timeout")
        try:
            response = requests.get(
                f"{base}{path}/{identifier}",
                headers={"x-api-key": self.api_key},
                timeout=timeout,
                allow_redirects=False,
                params=params,
            )
        except requests.RequestException as exc:
            raise MediaRequestError(
                f"Could not retrieve media task {identifier}"
            ) from exc
        data = _response(response, 200)
        if (
            data.get("task_id") != identifier
            or not isinstance(data.get("stage"), str)
            or not data["stage"]
        ):
            raise MediaRequestError(
                f"Media API returned an invalid status for task {identifier}",
                status_code=200,
            )
        if "error" in data and data["stage"] != "STAGE_FAILED":
            raise MediaRequestError(
                f"Media API returned an error: {data['error']}", status_code=200
            )
        return data

    def get_image_status(self, task_id: str, *, timeout: float = 10) -> ImageTaskStatus:
        """Retrieve one image task, including processing or terminal failure status."""
        return cast(
            ImageTaskStatus,
            self._media_status(IMAGE_API_ENDPOINT, "/v1/tasks", task_id, timeout),
        )

    def get_video_status(self, task_id: str, *, timeout: float = 10) -> VideoTaskStatus:
        """Retrieve one video task using the public 1.1 response format."""
        return cast(
            VideoTaskStatus,
            self._media_status(
                VIDEO_API_ENDPOINT,
                "/v1/video/tasks",
                task_id,
                timeout,
                params={"response_version": "1.1"},
            ),
        )

    def _wait_media(
        self,
        task_id: str,
        fetch: Callable[..., object],
        deadline: float,
        poll_interval: float,
    ) -> dict[str, object]:
        identifier = _task_id(task_id)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise MediaTaskTimeout(identifier)
            delay = poll_interval
            try:
                result = cast(
                    dict[str, object], fetch(identifier, timeout=min(10, remaining))
                )
            except MediaRequestError as exc:
                if (
                    exc.status_code is not None
                    and exc.status_code not in _RETRYABLE_STATUS_CODES
                ):
                    raise
                delay = max(delay, exc.retry_after)
            else:
                if result["stage"] == "STAGE_SUCCESS":
                    return result
                if result["stage"] == "STAGE_FAILED":
                    error = result.get("error")
                    if not isinstance(error, dict):
                        raise MediaRequestError(
                            f"Media task {identifier} failed without error details",
                            status_code=200,
                        )
                    raise MediaTaskError(identifier, error)
            time.sleep(min(delay, max(0, deadline - time.monotonic())))

    def wait_for_image(
        self, task_id: str, *, timeout: float = 300, poll_interval: float = 0.5
    ) -> ImageResult:
        """Wait for an accepted image task. Timeout exposes ``task_id`` for resuming.

        Only polling is retried, on transport errors and HTTP 429/5xx responses.
        A failed task raises :class:`MediaTaskError`; it is never resubmitted.
        """
        deadline = time.monotonic() + _positive(timeout, "timeout")
        return cast(
            ImageResult,
            self._wait_media(
                task_id,
                self.get_image_status,
                deadline,
                max(0.1, _positive(poll_interval, "poll_interval")),
            ),
        )

    def wait_for_video(
        self, task_id: str, *, timeout: float = 600, poll_interval: float = 1
    ) -> VideoResult:
        """Wait for an accepted video task; timeout and failure preserve its task ID."""
        deadline = time.monotonic() + _positive(timeout, "timeout")
        return cast(
            VideoResult,
            self._wait_media(
                task_id,
                self.get_video_status,
                deadline,
                max(0.1, _positive(poll_interval, "poll_interval")),
            ),
        )

    def predict_image(
        self,
        image: MediaInput,
        *,
        model: str,
        timeout: float = 300,
        poll_interval: float = 0.5,
    ) -> ImageResult:
        """Submit and wait for an image result using an explicit image model.

        ``timeout`` covers submission and polling. If polling expires,
        :class:`MediaTaskTimeout` provides the accepted task ID so you can
        resume with :meth:`wait_for_image` instead of submitting again.
        """
        timeout = _positive(timeout, "timeout")
        interval = max(0.1, _positive(poll_interval, "poll_interval"))
        deadline = time.monotonic() + timeout
        task = self.submit_image(image, model=model, timeout=timeout)
        return cast(
            ImageResult,
            self._wait_media(
                task["task_id"], self.get_image_status, deadline, interval
            ),
        )

    def predict_video(
        self,
        video: MediaInput,
        *,
        filename: str | None = None,
        timeout: float = 600,
        poll_interval: float = 1,
    ) -> VideoResult:
        """Stream a video file and wait for its analysis using server defaults.

        ``timeout`` covers submission and polling. On a polling timeout,
        resume :meth:`wait_for_video` with ``MediaTaskTimeout.task_id``.
        No video URL or processing options are required.
        """
        timeout = _positive(timeout, "timeout")
        interval = max(0.1, _positive(poll_interval, "poll_interval"))
        deadline = time.monotonic() + timeout
        task = self.submit_video(video, filename=filename, timeout=timeout)
        return cast(
            VideoResult,
            self._wait_media(
                task["task_id"], self.get_video_status, deadline, interval
            ),
        )
