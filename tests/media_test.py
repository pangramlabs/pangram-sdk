import base64
import inspect
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

import requests

from pangram import (
    ImageResult,
    MediaRequestError,
    MediaTaskError,
    MediaTaskTimeout,
    Pangram,
    PangramText,
    VideoResult,
)
from pangram.media import IMAGE_API_ENDPOINT, VIDEO_API_ENDPOINT

TASK_ID = "8db93921-df98-4edf-ae1d-8dd5839cd473"


def response(data, status=200, headers=None):
    result = requests.Response()
    result.status_code = status
    result._content = json.dumps(data).encode()
    result.headers.update(headers or {})
    return result


def success(kind="image"):
    if kind == "image":
        return {
            "task_id": TASK_ID,
            "stage": "STAGE_SUCCESS",
            "prediction": "No AI",
            "version": None,
            "ai_likelihood": None,
            "confidence": None,
            "heatmap": None,
            "detection_source": "c2pa",
            "metadata": {},
            "thumbnail": None,
        }
    return {
        "task_id": TASK_ID,
        "stage": "STAGE_SUCCESS",
        "schema_version": "1.1",
        "prediction_short": "no_ai",
        "headline": "No AI detected",
        "version": "image-flash-1",
        "frames": [],
        "segments": [],
        "fraction_ai": 0.0,
        "fraction_human": 1.0,
        "fraction_mixed": 0.0,
        "detailed_labels": True,
    }


class Clock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, duration):
        self.sleeps.append(duration)
        self.now += duration


class TestMedia(unittest.TestCase):
    def setUp(self):
        self.client = Pangram(api_key="test-key")

    def test_public_methods_and_response_types(self):
        self.assertIs(Pangram, PangramText)
        self.assertIn("prediction", ImageResult.__required_keys__)
        self.assertIn("frames", VideoResult.__required_keys__)
        for name in ("submit_image", "predict_image"):
            parameter = inspect.signature(getattr(Pangram, name)).parameters["model"]
            self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
            self.assertIs(parameter.default, inspect.Parameter.empty)
        for name in ("submit_video", "predict_video"):
            self.assertFalse(
                {"video_url", "sampling_fps", "hmm_smoothing", "detailed_labels"}
                & set(inspect.signature(getattr(Pangram, name)).parameters)
            )

    def test_image_models_are_sent_explicitly(self):
        for model in (
            "pangram-image-1",
            "pangram-image-flash-1",
            "pangram-image-0.2",
            "default",
        ):
            with self.subTest(model=model), patch(
                "pangram.media.requests.post",
                return_value=response({"task_id": TASK_ID}, 202),
            ) as post:
                result = self.client.submit_image(b"image bytes", model=model)
                self.assertEqual(result, {"task_id": TASK_ID})
                self.assertEqual(
                    post.call_args.args, (IMAGE_API_ENDPOINT + "/v1/tasks",)
                )
                self.assertEqual(
                    post.call_args.kwargs["json"],
                    {
                        "image_b64": base64.b64encode(b"image bytes").decode(),
                        "model": model,
                    },
                )
                self.assertEqual(
                    post.call_args.kwargs["headers"], {"x-api-key": "test-key"}
                )
                self.assertFalse(post.call_args.kwargs["allow_redirects"])

    def test_image_paths_and_borrowed_streams(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "image.png"
            path.write_bytes(b"image")
            with patch(
                "pangram.media.requests.post",
                return_value=response({"task_id": TASK_ID}, 202),
            ):
                self.client.submit_image(path, model="pangram-image-1")
                stream = io.BytesIO(b"prefix-image")
                stream.seek(7)
                self.client.submit_image(stream, model="pangram-image-1")
                self.assertFalse(stream.closed)

    def test_image_validation_occurs_before_submission(self):
        with patch("pangram.media.requests.post") as post:
            for value in (b"", io.StringIO("not binary"), object()):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    self.client.submit_image(value, model="pangram-image-1")
            for model in (None, "", " ", 4, "m" * 201):
                with self.subTest(model=model), self.assertRaises(ValueError):
                    self.client.submit_image(b"image", model=model)
            with patch("pangram._media_input.MAX_IMAGE_BYTES", 3), self.assertRaises(
                ValueError
            ):
                self.client.submit_image(b"four", model="pangram-image-1")
            post.assert_not_called()

    def test_video_formats_and_stream_ownership(self):
        for extension, mime in (
            (".mp4", "video/mp4"),
            (".mov", "video/quicktime"),
            (".webm", "video/webm"),
        ):
            with self.subTest(
                extension=extension
            ), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / ("clip" + extension)
                path.write_bytes(b"video payload")

                def submit(url, **kwargs):
                    self.assertEqual(url, VIDEO_API_ENDPOINT + "/v1/video/tasks")
                    body = kwargs["data"].to_string()
                    self.assertIn(b'name="file"', body)
                    self.assertIn(mime.encode(), body)
                    self.assertIn(b"video payload", body)
                    self.assertNotIn(b"detailed_labels", body)
                    self.assertNotIn("files", kwargs)
                    self.assertTrue(
                        kwargs["headers"]["Content-Type"].startswith(
                            "multipart/form-data; boundary="
                        )
                    )
                    return response({"task_id": TASK_ID}, 202)

                with patch("pangram.media.requests.post", side_effect=submit):
                    self.client.submit_video(path)
                    stream = io.BytesIO(b"video payload")
                    self.client.submit_video(stream, filename="clip" + extension)
                    self.assertFalse(stream.closed)
                    self.client.submit_video(
                        b"video payload", filename="clip" + extension
                    )

    def test_large_video_is_not_read_before_request(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "large.mp4"
            with path.open("wb") as file:
                file.truncate(500 * 1024 * 1024)
            with path.open("rb") as file:

                def submit(url, **kwargs):
                    self.assertEqual(file.tell(), 0)
                    self.assertGreater(kwargs["data"].len, 500 * 1024 * 1024)
                    self.assertLess(len(kwargs["data"].read(32)), 33)
                    return response({"task_id": TASK_ID}, 202)

                with patch("pangram.media.requests.post", side_effect=submit):
                    self.client.submit_video(file)
                    self.assertFalse(file.closed)

    def test_video_validation(self):
        with patch("pangram.media.requests.post") as post:
            for data, name in (
                (b"", "clip.mp4"),
                (b"x", None),
                (b"x", "clip.txt"),
                (b"x", "bad\n.mp4"),
            ):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    self.client.submit_video(data, filename=name)
            with self.assertRaises(ValueError):
                self.client.submit_video(io.StringIO("text"), filename="clip.mp4")
            with patch("pangram._media_input.MAX_VIDEO_BYTES", 3), self.assertRaises(
                ValueError
            ):
                self.client.submit_video(b"four", filename="clip.mp4")
            post.assert_not_called()

    def test_video_borrowed_file_respects_current_position(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "clip.mp4"
            path.write_bytes(b"prefix-payload")
            with path.open("rb") as file:
                file.seek(7)

                def submit(url, **kwargs):
                    body = kwargs["data"].to_string()
                    self.assertIn(b"payload", body)
                    self.assertNotIn(b"prefix-", body)
                    return response({"task_id": TASK_ID}, 202)

                with patch("pangram.media.requests.post", side_effect=submit):
                    self.client.submit_video(file)

    def test_owned_video_file_closes_on_error_and_submission_is_not_retried(self):
        files = []
        actual_open = open

        def tracked_open(*args, **kwargs):
            file = actual_open(*args, **kwargs)
            files.append(file)
            return file

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "clip.mp4"
            path.write_bytes(b"video")
            with patch("pangram._media_input.open", side_effect=tracked_open), patch(
                "pangram.media.requests.post",
                side_effect=requests.Timeout("lost response"),
            ) as post:
                with self.assertRaises(MediaRequestError):
                    self.client.predict_video(path)
                self.assertEqual(post.call_count, 1)
            self.assertTrue(files[0].closed)

    def test_image_submission_is_not_retried(self):
        with patch(
            "pangram.media.requests.post", side_effect=requests.Timeout()
        ) as post:
            with self.assertRaises(MediaRequestError):
                self.client.predict_image(b"image", model="pangram-image-1")
            self.assertEqual(post.call_count, 1)

    def test_get_status_returns_failed_task_and_pins_video_schema(self):
        failed = {
            "task_id": TASK_ID,
            "stage": "STAGE_FAILED",
            "error": {
                "error": "bad file",
                "error_code": "invalid_image",
                "retryable": False,
            },
        }
        with patch("pangram.media.requests.get", return_value=response(failed)) as get:
            self.assertEqual(self.client.get_video_status(TASK_ID), failed)
            self.assertEqual(
                get.call_args.kwargs["params"], {"response_version": "1.1"}
            )
            self.assertEqual(get.call_args.kwargs["headers"], {"x-api-key": "test-key"})
        with patch(
            "pangram.media.requests.get",
            return_value=response({"error": "denied"}, 403),
        ):
            with self.assertRaises(MediaRequestError) as caught:
                self.client.get_image_status(TASK_ID)
            self.assertEqual(caught.exception.status_code, 403)

    def test_invalid_task_ids_and_timing_do_not_make_requests(self):
        with patch("pangram.media.requests.get") as get, patch(
            "pangram.media.requests.post"
        ) as post:
            for identifier in ("", "../task", "not-a-uuid", None):
                with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                    self.client.get_video_status(identifier)
            for value in (0, -1, float("nan"), float("inf"), True, "30"):
                with self.subTest(timeout=value), self.assertRaises(ValueError):
                    self.client.predict_video(
                        b"video", filename="clip.mp4", timeout=value
                    )
                with self.subTest(interval=value), self.assertRaises(ValueError):
                    self.client.predict_image(
                        b"image", model="pangram-image-1", poll_interval=value
                    )
            get.assert_not_called()
            post.assert_not_called()

    def test_predict_returns_original_results_including_nullable_provenance(self):
        for kind in ("image", "video"):
            result = success(kind)
            result["future_field"] = "preserved"
            with self.subTest(kind=kind), patch(
                "pangram.media.requests.post",
                return_value=response({"task_id": TASK_ID}, 202),
            ) as post, patch(
                "pangram.media.requests.get", return_value=response(result)
            ):
                if kind == "image":
                    actual = self.client.predict_image(
                        b"image", model="pangram-image-flash-1"
                    )
                    self.assertIsNone(actual["ai_likelihood"])
                else:
                    actual = self.client.predict_video(b"video", filename="clip.mp4")
                self.assertEqual(actual, result)
                self.assertEqual(post.call_count, 1)

    def test_terminal_failure_preserves_task_id_and_error(self):
        error = {
            "error": "invalid media",
            "error_code": "invalid_image",
            "retryable": False,
        }
        with patch(
            "pangram.media.requests.get",
            return_value=response(
                {"task_id": TASK_ID, "stage": "STAGE_FAILED", "error": error}
            ),
        ):
            with self.assertRaises(MediaTaskError) as caught:
                self.client.wait_for_image(TASK_ID)
        self.assertEqual(caught.exception.task_id, TASK_ID)
        self.assertEqual(caught.exception.error, error)

    def test_polling_retries_transient_errors_and_honors_retry_after(self):
        clock = Clock()
        responses = [
            requests.ConnectionError(),
            response({}, 503),
            response({}, 429, {"Retry-After": "2"}),
            response(success("video")),
        ]
        with patch("pangram.media.time.monotonic", side_effect=clock.monotonic), patch(
            "pangram.media.time.sleep", side_effect=clock.sleep
        ), patch("pangram.media.requests.get", side_effect=responses), patch(
            "pangram.media.requests.post"
        ) as post:
            self.assertEqual(
                self.client.wait_for_video(TASK_ID, timeout=10), success("video")
            )
            self.assertEqual(clock.sleeps, [1, 1, 2])
            post.assert_not_called()

    def test_timeout_retains_task_id_and_can_be_resumed_without_resubmitting(self):
        clock = Clock()
        pending = {
            "task_id": TASK_ID,
            "stage": "STAGE_VIDEO_INFERENCE",
            "frames_processed": 1,
            "total_frames": 10,
        }
        with patch("pangram.media.time.monotonic", side_effect=clock.monotonic), patch(
            "pangram.media.time.sleep", side_effect=clock.sleep
        ), patch(
            "pangram.media.requests.post",
            return_value=response({"task_id": TASK_ID}, 202),
        ) as post, patch(
            "pangram.media.requests.get", return_value=response(pending)
        ) as get:
            with self.assertRaises(MediaTaskTimeout) as caught:
                self.client.predict_video(b"video", filename="clip.mp4", timeout=2)
            self.assertEqual(caught.exception.task_id, TASK_ID)
            self.assertEqual(post.call_count, 1)
            self.assertTrue(
                all(call.kwargs["timeout"] <= 2 for call in get.call_args_list)
            )
            get.return_value = response(success("video"))
            self.assertEqual(
                self.client.wait_for_video(caught.exception.task_id), success("video")
            )
            self.assertEqual(post.call_count, 1)

    def test_invalid_responses_fail_without_polling_forever(self):
        for data in (
            [],
            {},
            {"task_id": TASK_ID},
            {"task_id": "other", "stage": "STAGE_SUCCESS"},
        ):
            with self.subTest(data=data), patch(
                "pangram.media.requests.get", return_value=response(data)
            ), self.assertRaises(MediaRequestError):
                self.client.wait_for_image(TASK_ID)
        with patch(
            "pangram.media.requests.post", return_value=response({}, 202)
        ), self.assertRaises(MediaRequestError):
            self.client.submit_image(b"image", model="pangram-image-1")

    def test_submission_time_consumes_convenience_timeout_budget(self):
        clock = Clock()

        def submitted(*args, **kwargs):
            clock.now = 5
            return response({"task_id": TASK_ID}, 202)

        with patch("pangram.media.time.monotonic", side_effect=clock.monotonic), patch(
            "pangram.media.requests.post", side_effect=submitted
        ), patch("pangram.media.requests.get") as get:
            with self.assertRaises(MediaTaskTimeout) as caught:
                self.client.predict_image(b"image", model="pangram-image-1", timeout=1)
            self.assertEqual(caught.exception.task_id, TASK_ID)
            get.assert_not_called()

    def test_non_json_polling_failure_honors_retry_delay_and_deadline(self):
        clock = Clock()
        unavailable = requests.Response()
        unavailable.status_code = 503
        unavailable.headers["Retry-After"] = "10"
        unavailable._content = b"temporarily unavailable"
        with patch("pangram.media.time.monotonic", side_effect=clock.monotonic), patch(
            "pangram.media.time.sleep", side_effect=clock.sleep
        ), patch("pangram.media.requests.get", return_value=unavailable):
            with self.assertRaises(MediaTaskTimeout) as caught:
                self.client.wait_for_video(TASK_ID, timeout=3)
        self.assertEqual(caught.exception.task_id, TASK_ID)
        self.assertEqual(clock.sleeps, [3])

    def test_http_submission_errors_are_not_retried(self):
        for status in (400, 401, 402, 429, 500, 503):
            with self.subTest(status=status), patch(
                "pangram.media.requests.post",
                return_value=response({"error": "rejected"}, status),
            ) as post, patch("pangram.media.requests.get") as get:
                with self.assertRaises(MediaRequestError) as caught:
                    self.client.predict_image(b"image", model="pangram-image-1")
                self.assertEqual(caught.exception.status_code, status)
                self.assertEqual(post.call_count, 1)
                get.assert_not_called()


class TestRealHTTPMedia(unittest.TestCase):
    def test_json_and_streamed_multipart_use_the_real_requests_transport(self):
        received = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                received.append((self.path, self.headers, body))
                self.reply({"task_id": TASK_ID}, 202)

            def do_GET(self):
                received.append((self.path, self.headers, None))
                self.reply(success("video" if "/video/" in self.path else "image"))

            def reply(self, data, status=200):
                body = json.dumps(data).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            endpoint = f"http://127.0.0.1:{server.server_port}"
            try:
                with patch("pangram.media.IMAGE_API_ENDPOINT", endpoint), patch(
                    "pangram.media.VIDEO_API_ENDPOINT", endpoint
                ):
                    client = Pangram(api_key="local-contract-key")
                    client.predict_image(b"image", model="pangram-image-1")
                    client.predict_video(b"video payload", filename="clip.mp4")
            finally:
                server.shutdown()
                thread.join()
        self.assertEqual(len(received), 4)
        self.assertEqual(json.loads(received[0][2])["model"], "pangram-image-1")
        self.assertIn(b"video payload", received[2][2])
        self.assertEqual(
            received[2][2].count(b"Content-Disposition: form-data; name="), 1
        )
        self.assertIn("response_version=1.1", received[3][0])
        self.assertTrue(
            all(item[1]["x-api-key"] == "local-contract-key" for item in received)
        )


if __name__ == "__main__":
    unittest.main()
