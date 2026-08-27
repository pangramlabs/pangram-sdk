import inspect
import os
import tempfile
import unittest
import warnings
from unittest.mock import call, patch

import requests

from pangram import (
    BulkResultItem,
    BulkResults,
    BulkResultsPage,
    Pangram,
    PangramText,
    PredictionResult,
    PredictionWindow,
)
from pangram.text_classifier import (
    API_ENDPOINT,
    FILE_UPLOAD_API_ENDPOINT,
    HTTP_REQUEST_TIMEOUT_SECONDS,
    MIN_POLL_INTERVAL_SECONDS,
)


class MockResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        return self._json_data


def pangram_4_success_response() -> dict[str, object]:
    return {
        "stage": "STAGE_SUCCESS",
        "text": "hello",
        "version": "4.0",
        "headline": "Human Written",
        "prediction": "We believe this text is human-written.",
        "prediction_short": "Human",
        "fraction_ai": 0.0,
        "fraction_ai_assisted": 0.0,
        "fraction_human": 1.0,
        "num_ai_segments": 0,
        "num_ai_assisted_segments": 0,
        "num_human_segments": 1,
        "windows": [
            {
                "text": "hello",
                "label": "Human Written",
                "ai_assistance_score": 0.0,
                "confidence": "High",
                "start_index": 0,
                "end_index": 5,
                "word_count": 1,
                "token_length": 1,
                "is_humanized": False,
                "humanizer_score": 0.0,
            }
        ],
    }


def model_selection_warnings(
    recorded_warnings: list[warnings.WarningMessage],
) -> list[warnings.WarningMessage]:
    matching_warnings = []
    for recorded_warning in recorded_warnings:
        message = str(recorded_warning.message).lower()
        if (
            issubclass(recorded_warning.category, DeprecationWarning)
            and "model" in message
            and "required" in message
            and "september 30" in message
        ):
            matching_warnings.append(recorded_warning)
    return matching_warnings


class TestModelSelectionContract(unittest.TestCase):
    def test_only_model_is_keyword_only_for_detection_requests(self):
        legacy_positional_parameters = {
            "predict": ("text", "public_dashboard_link", "timeout", "poll_interval"),
            "predict_with_dashboard_link": ("text", "timeout", "poll_interval"),
            "predict_short": ("text",),
            "batch_predict": ("text_batch",),
            "submit_bulk": ("text", "items"),
        }

        for method_name, positional_parameter_names in (
            legacy_positional_parameters.items()
        ):
            with self.subTest(method=method_name):
                parameters = inspect.signature(
                    getattr(PangramText, method_name)
                ).parameters
                model_parameter = parameters["model"]
                self.assertEqual(model_parameter.kind, inspect.Parameter.KEYWORD_ONLY)
                self.assertIsNone(model_parameter.default)
                for parameter_name in positional_parameter_names:
                    self.assertEqual(
                        parameters[parameter_name].kind,
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    )

    def test_prediction_types_are_public(self):
        self.assertIn("stage", PredictionResult.__required_keys__)
        self.assertIn("is_humanized", PredictionWindow.__optional_keys__)
        self.assertIn("humanizer_score", PredictionWindow.__optional_keys__)
        self.assertIn("result", BulkResultItem.__required_keys__)
        self.assertIn("items", BulkResultsPage.__required_keys__)
        self.assertIn("items", BulkResults.__required_keys__)

    def test_file_detection_methods_do_not_accept_model(self):
        for method_name in ("predict_file", "predict_files"):
            with self.subTest(method=method_name):
                parameters = inspect.signature(
                    getattr(PangramText, method_name)
                ).parameters
                self.assertNotIn("model", parameters)

    def test_predict_rejects_invalid_models_before_request(self):
        pangram_client = Pangram(api_key="test-key")

        for invalid_model in ("", "  ", 4):
            with self.subTest(model=invalid_model), patch(
                "pangram.text_classifier.requests.post",
            ) as mock_post:
                with self.assertRaisesRegex(
                    ValueError,
                    "model must be a non-empty string",
                ):
                    pangram_client.predict("hello", model=invalid_model)
                mock_post.assert_not_called()

    def test_batch_predict_validates_model_for_an_empty_batch(self):
        pangram_client = Pangram(api_key="test-key")

        with self.assertWarns(DeprecationWarning):
            with self.assertRaisesRegex(
                ValueError,
                "model must be a non-empty string",
            ):
                pangram_client.batch_predict([], model=" ")


class TestOptionalModelCompatibility(unittest.TestCase):
    def assert_single_model_selection_warning(
        self,
        recorded_warnings: list[warnings.WarningMessage],
    ) -> None:
        self.assertEqual(
            len(model_selection_warnings(recorded_warnings)),
            1,
            [str(recorded_warning.message) for recorded_warning in recorded_warnings],
        )

    def test_predict_without_model_warns_and_omits_selector(self):
        pangram_client = Pangram(api_key="test-key")
        success_response = pangram_4_success_response()

        with patch(
            "pangram.text_classifier.requests.post",
            return_value=MockResponse(json_data={"task_id": "task-1"}),
        ) as mock_post, patch(
            "pangram.text_classifier.requests.get",
            return_value=MockResponse(json_data=success_response),
        ), warnings.catch_warnings(record=True) as recorded_warnings:
            warnings.simplefilter("always")
            result = pangram_client.predict("hello")

        self.assertEqual(
            mock_post.call_args.kwargs["json"],
            {"text": "hello", "public_dashboard_link": False},
        )
        self.assert_single_model_selection_warning(recorded_warnings)
        self.assertEqual(result, success_response)

    def test_legacy_predict_positional_dashboard_flag_warns_and_omits_selector(self):
        pangram_client = Pangram(api_key="test-key")
        success_response = pangram_4_success_response()

        with patch(
            "pangram.text_classifier.requests.post",
            return_value=MockResponse(json_data={"task_id": "task-1"}),
        ) as mock_post, patch(
            "pangram.text_classifier.requests.get",
            return_value=MockResponse(json_data=success_response),
        ), warnings.catch_warnings(record=True) as recorded_warnings:
            warnings.simplefilter("always")
            result = pangram_client.predict("hello", True)

        self.assertEqual(
            mock_post.call_args.kwargs["json"],
            {"text": "hello", "public_dashboard_link": True},
        )
        self.assert_single_model_selection_warning(recorded_warnings)
        self.assertEqual(result, success_response)

    def test_legacy_dashboard_timeout_forwards_through_public_predict(self):
        pangram_client = Pangram(api_key="test-key")
        success_response = pangram_4_success_response()
        success_response["dashboard_link"] = (
            "https://www.pangram.com/history/query-1"
        )

        with patch.object(
            PangramText,
            "predict",
            return_value=success_response,
        ) as mock_predict, warnings.catch_warnings(
            record=True,
        ) as recorded_warnings:
            warnings.simplefilter("always")
            result = pangram_client.predict_with_dashboard_link("hello", 30)

        mock_predict.assert_called_once()
        self.assertEqual(mock_predict.call_args.args, ("hello",))
        self.assertTrue(mock_predict.call_args.kwargs["public_dashboard_link"])
        self.assertEqual(mock_predict.call_args.kwargs["timeout"], 30)
        self.assertNotIn("model", mock_predict.call_args.kwargs)
        self.assert_single_model_selection_warning(recorded_warnings)
        self.assertEqual(result, success_response)

    def test_predict_short_without_model_forwards_through_public_predict(self):
        pangram_client = Pangram(api_key="test-key")
        success_response = pangram_4_success_response()

        with patch.object(
            PangramText,
            "predict",
            return_value=success_response,
        ) as mock_predict, warnings.catch_warnings(
            record=True,
        ) as recorded_warnings:
            warnings.simplefilter("always")
            result = pangram_client.predict_short("hello")

        mock_predict.assert_called_once_with("hello")
        self.assert_single_model_selection_warning(recorded_warnings)
        self.assertTrue(
            any(
                "predict_short" in str(recorded_warning.message)
                for recorded_warning in recorded_warnings
            )
        )
        self.assertEqual(result, success_response)

    def test_batch_predict_without_model_forwards_through_public_predict(self):
        pangram_client = Pangram(api_key="test-key")
        success_response = pangram_4_success_response()

        with patch.object(
            PangramText,
            "predict",
            side_effect=[success_response, success_response],
        ) as mock_predict, warnings.catch_warnings(
            record=True,
        ) as recorded_warnings:
            warnings.simplefilter("always")
            results = pangram_client.batch_predict(["first", "second"])

        self.assertEqual(
            mock_predict.call_args_list,
            [call("first"), call("second")],
        )
        self.assert_single_model_selection_warning(recorded_warnings)
        self.assertTrue(
            any(
                "batch_predict" in str(recorded_warning.message)
                for recorded_warning in recorded_warnings
            )
        )
        self.assertEqual(results, [success_response, success_response])

    def test_submit_bulk_without_model_warns_and_omits_selector(self):
        pangram_client = Pangram(api_key="test-key")
        bulk_response = {
            "bulk_id": "blk_123",
            "status": "queued",
            "total_items": 1,
            "accepted_items": [
                {"index": 0, "id": None, "task_id": "task-1"},
            ],
            "failed_items": [],
        }

        with patch(
            "pangram.text_classifier.requests.post",
            return_value=MockResponse(status_code=202, json_data=bulk_response),
        ) as mock_post, warnings.catch_warnings(
            record=True,
        ) as recorded_warnings:
            warnings.simplefilter("always")
            result = pangram_client.submit_bulk(["hello"])

        self.assertEqual(mock_post.call_args.kwargs["json"], {"text": ["hello"]})
        self.assert_single_model_selection_warning(recorded_warnings)
        self.assertEqual(result, bulk_response)

    def test_submit_bulk_items_without_model_warns_and_omits_selector(self):
        pangram_client = Pangram(api_key="test-key")
        bulk_response = {
            "bulk_id": "blk_123",
            "status": "queued",
            "total_items": 1,
            "accepted_items": [
                {"index": 0, "id": "row-1", "task_id": "task-1"},
            ],
            "failed_items": [],
        }

        with patch(
            "pangram.text_classifier.requests.post",
            return_value=MockResponse(status_code=202, json_data=bulk_response),
        ) as mock_post, warnings.catch_warnings(
            record=True,
        ) as recorded_warnings:
            warnings.simplefilter("always")
            result = pangram_client.submit_bulk(
                items=[{"id": "row-1", "text": "hello"}],
            )

        self.assertEqual(
            mock_post.call_args.kwargs["json"],
            {"items": [{"id": "row-1", "text": "hello"}]},
        )
        self.assert_single_model_selection_warning(recorded_warnings)
        self.assertEqual(result, bulk_response)

    def test_explicit_model_does_not_emit_model_selection_warning(self):
        pangram_client = Pangram(api_key="test-key")
        success_response = pangram_4_success_response()
        bulk_response = {
            "bulk_id": "blk_123",
            "status": "queued",
            "total_items": 1,
            "accepted_items": [
                {"index": 0, "id": None, "task_id": "task-1"},
            ],
            "failed_items": [],
        }

        with patch.object(
            PangramText,
            "_submit_prediction_task",
            return_value="task-1",
        ), patch.object(
            PangramText,
            "_poll_prediction_task",
            return_value=success_response,
        ), patch(
            "pangram.text_classifier.requests.post",
            return_value=MockResponse(status_code=202, json_data=bulk_response),
        ), warnings.catch_warnings(record=True) as recorded_warnings:
            warnings.simplefilter("always")
            pangram_client.predict("hello", model="pangram-4")
            pangram_client.predict_with_dashboard_link(
                "hello",
                model="pangram-4",
            )
            pangram_client.predict_short("hello", model="pangram-4")
            pangram_client.batch_predict(["hello"], model="pangram-4")
            pangram_client.submit_bulk(model="pangram-4", text=["hello"])

        self.assertEqual(model_selection_warnings(recorded_warnings), [])


class TestPredict(unittest.TestCase):
    def test_predict(self):
        text = "I recently had the pleasure of visiting OpenAI. As an AI language model, I cannot actually visit places."
        pangram_client = Pangram(api_key="test-key")
        success_response = {
            "stage": "STAGE_SUCCESS",
            "text": text,
            "version": "4.0",
            "headline": "AI Detected",
            "prediction": "We believe this is mixed content",
            "prediction_short": "Mixed",
            "fraction_ai": 0.2,
            "fraction_ai_assisted": 0.3,
            "fraction_human": 0.5,
            "num_ai_segments": 1,
            "num_ai_assisted_segments": 2,
            "num_human_segments": 3,
            "windows": [
                {
                    "text": "I recently had the pleasure of visiting OpenAI.",
                    "label": "AI-Generated",
                    "ai_assistance_score": 0.92,
                    "confidence": "High",
                    "start_index": 0,
                    "end_index": 45,
                    "word_count": 8,
                    "token_length": 10,
                    "is_humanized": False,
                    "humanizer_score": 0.0,
                }
            ],
        }

        with patch(
            "pangram.text_classifier.requests.post",
            return_value=MockResponse(json_data={"task_id": "task-1"}),
        ) as mock_post, patch(
            "pangram.text_classifier.requests.get",
            side_effect=[
                MockResponse(json_data={"task_id": "task-1", "stage": "STAGE_PREPROCESSING"}),
                MockResponse(json_data=success_response),
            ],
        ), patch("pangram.text_classifier.time.sleep") as mock_sleep:
            result = pangram_client.predict(text, model="pangram-4", poll_interval=0)

        self.assertEqual(mock_post.call_args.args[0], f"{API_ENDPOINT}/task")
        self.assertEqual(mock_post.call_args.kwargs["json"], {
            "text": text,
            "model": "pangram-4",
            "public_dashboard_link": False,
        })
        self.assertEqual(mock_post.call_args.kwargs["headers"]["x-api-key"], "test-key")
        mock_sleep.assert_called_once_with(MIN_POLL_INTERVAL_SECONDS)
        self.assertEqual(result, success_response)
        self.assertIs(result["windows"][0]["is_humanized"], False)
        self.assertEqual(result["windows"][0]["humanizer_score"], 0.0)

    def test_predict_normalizes_model_whitespace(self):
        pangram_client = Pangram(api_key="test-key")
        success_response = {
            "stage": "STAGE_SUCCESS",
            "text": "hello",
            "version": "4.0",
            "headline": "Human Written",
            "prediction": "We believe this text is human-written.",
            "prediction_short": "Human",
            "fraction_ai": 0.0,
            "fraction_ai_assisted": 0.0,
            "fraction_human": 1.0,
            "num_ai_segments": 0,
            "num_ai_assisted_segments": 0,
            "num_human_segments": 1,
            "windows": [],
        }

        with patch(
            "pangram.text_classifier.requests.post",
            return_value=MockResponse(json_data={"task_id": "task-1"}),
        ) as mock_post, patch(
            "pangram.text_classifier.requests.get",
            return_value=MockResponse(json_data=success_response),
        ):
            pangram_client.predict("hello", model=" pangram-4 ")

        self.assertEqual(mock_post.call_args.kwargs["json"]["model"], "pangram-4")

    def test_predict_propagates_model_selection_errors(self):
        pangram_client = Pangram(api_key="test-key")

        for status_code, message in (
            (422, "unknown model"),
            (403, "Requested model is not enabled for this API key"),
            (503, "Requested model is not currently available"),
        ):
            with self.subTest(status_code=status_code), patch(
                "pangram.text_classifier.requests.post",
                return_value=MockResponse(
                    status_code=status_code,
                    text=message,
                ),
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    rf"\[{status_code}\].*{message}",
                ):
                    pangram_client.predict("hello", model="pangram-4")

    def test_predict_raises_when_async_task_fails(self):
        pangram_client = Pangram(api_key="test-key")
        with patch(
            "pangram.text_classifier.requests.post",
            return_value=MockResponse(json_data={"task_id": "task-1"}),
        ), patch(
            "pangram.text_classifier.requests.get",
            return_value=MockResponse(json_data={
                "task_id": "task-1",
                "stage": "STAGE_FAILED",
                "headline": "processing failed",
            }),
        ):
            with self.assertRaisesRegex(ValueError, "processing failed"):
                pangram_client.predict("hello", model="default", poll_interval=0)

    def test_predict_rejects_invalid_timeout(self):
        pangram_client = Pangram(api_key="test-key")
        with self.assertRaisesRegex(ValueError, "timeout must be greater than 0"):
            pangram_client.predict("hello", model="default", timeout=0)

    def test_predict_wraps_submit_request_errors(self):
        pangram_client = Pangram(api_key="test-key")
        with patch(
            "pangram.text_classifier.requests.post",
            side_effect=requests.exceptions.Timeout("timed out"),
        ):
            with self.assertRaisesRegex(ValueError, "submitting prediction task: timed out"):
                pangram_client.predict("hello", model="default")

    def test_predict_retries_poll_request_errors(self):
        pangram_client = Pangram(api_key="test-key")
        success_response = {
            "stage": "STAGE_SUCCESS",
            "text": "hello",
            "version": "3.3",
            "headline": "Human Written",
            "prediction": "We believe this text is human-written.",
            "prediction_short": "Human",
            "fraction_ai": 0.0,
            "fraction_ai_assisted": 0.0,
            "fraction_human": 1.0,
            "num_ai_segments": 0,
            "num_ai_assisted_segments": 0,
            "num_human_segments": 1,
            "windows": [],
        }
        with patch(
            "pangram.text_classifier.requests.post",
            return_value=MockResponse(json_data={"task_id": "task-1"}),
        ), patch(
            "pangram.text_classifier.requests.get",
            side_effect=[
                requests.exceptions.ConnectionError("connection dropped"),
                MockResponse(json_data=success_response),
            ],
        ), patch("pangram.text_classifier.time.sleep") as mock_sleep:
            result = pangram_client.predict("hello", model="default", poll_interval=0)

        mock_sleep.assert_called_once_with(MIN_POLL_INTERVAL_SECONDS)
        self.assertEqual(result, success_response)

    def test_predict_short_forwards_to_predict(self):
        text = "hello!"
        pangram_client = Pangram(api_key="test-key")
        with patch.object(PangramText, "predict", return_value={"text": text}) as mock_predict:
            with self.assertWarnsRegex(DeprecationWarning, "predict_short"):
                result = pangram_client.predict_short(text, model="pangram-4")

        mock_predict.assert_called_once_with(text, model="pangram-4")
        self.assertEqual(result, {"text": text})

class TestBatchPredict(unittest.TestCase):
    def test_batch_predict(self):
        text1 = "I recently had the pleasure of visiting OpenAI. As an AI language model, I cannot actually visit places."
        text2 = "i'm a human"
        text_batch = [text1, text2]
        pangram_client = Pangram(api_key="test-key")
        with patch.object(
            PangramText,
            "predict",
            side_effect=[{"text": text1}, {"text": text2}],
        ) as mock_predict:
            with self.assertWarnsRegex(DeprecationWarning, "batch_predict"):
                results = pangram_client.batch_predict(text_batch, model="pangram-4")

        self.assertEqual(
            mock_predict.call_args_list,
            [
                call(text1, model="pangram-4"),
                call(text2, model="pangram-4"),
            ],
        )
        self.assertEqual(len(results), len(text_batch))


class TestModelCatalog(unittest.TestCase):
    def test_list_models(self):
        pangram_client = Pangram(api_key="test-key")
        models_response = {"models": ["default", "pangram-4"]}

        with patch(
            "pangram.text_classifier.requests.get",
            return_value=MockResponse(json_data=models_response),
        ) as mock_get:
            result = pangram_client.list_models()

        self.assertEqual(mock_get.call_args.args[0], f"{API_ENDPOINT}/models")
        self.assertEqual(mock_get.call_args.kwargs["headers"]["x-api-key"], "test-key")
        self.assertEqual(
            mock_get.call_args.kwargs["timeout"],
            HTTP_REQUEST_TIMEOUT_SECONDS,
        )
        self.assertEqual(result, ["default", "pangram-4"])

    def test_list_models_accepts_future_model_ids(self):
        pangram_client = Pangram(api_key="test-key")
        models_response = {
            "models": ["default", "pangram-future"],
            "additional_metadata": {"ignored": True},
        }

        with patch(
            "pangram.text_classifier.requests.get",
            return_value=MockResponse(json_data=models_response),
        ):
            result = pangram_client.list_models()

        self.assertEqual(result, ["default", "pangram-future"])

    def test_list_models_propagates_api_errors(self):
        pangram_client = Pangram(api_key="test-key")

        for status_code, message in (
            (401, "invalid API key"),
            (402, "insufficient credits"),
        ):
            with self.subTest(status_code=status_code), patch(
                "pangram.text_classifier.requests.get",
                return_value=MockResponse(
                    status_code=status_code,
                    text=message,
                ),
            ), self.assertRaisesRegex(
                ValueError,
                rf"\[{status_code}\] {message}",
            ):
                pangram_client.list_models()

    def test_list_models_wraps_request_errors(self):
        pangram_client = Pangram(api_key="test-key")

        with patch(
            "pangram.text_classifier.requests.get",
            side_effect=requests.exceptions.Timeout("timed out"),
        ):
            with self.assertRaisesRegex(ValueError, "listing models: timed out"):
                pangram_client.list_models()

    def test_list_models_rejects_malformed_responses(self):
        pangram_client = Pangram(api_key="test-key")
        malformed_responses = (
            None,
            [],
            {},
            {"models": "default"},
            {"models": []},
            {"models": ["pangram-4"]},
            {"models": ["default", "default"]},
            {"models": ["default", " "]},
            {"models": ["default", 4]},
        )

        for malformed_response in malformed_responses:
            with self.subTest(response=malformed_response), patch(
                "pangram.text_classifier.requests.get",
                return_value=MockResponse(json_data=malformed_response),
            ):
                with self.assertRaises(ValueError):
                    pangram_client.list_models()


class TestBulkAPI(unittest.TestCase):
    def test_submit_bulk_with_text_list(self):
        pangram_client = Pangram(api_key="test-key")
        bulk_response = {
            "bulk_id": "blk_123",
            "status": "queued",
            "total_items": 2,
            "accepted_items": [
                {"index": 0, "id": None, "task_id": "task-1"},
                {"index": 1, "id": None, "task_id": "task-2"},
            ],
            "failed_items": [],
        }

        with patch(
            "pangram.text_classifier.requests.post",
            return_value=MockResponse(status_code=202, json_data=bulk_response),
        ) as mock_post:
            result = pangram_client.submit_bulk(
                model="pangram-4",
                text=["hello", "world"],
            )

        self.assertEqual(mock_post.call_args.args[0], f"{API_ENDPOINT}/bulk")
        self.assertEqual(mock_post.call_args.kwargs["json"], {
            "text": ["hello", "world"],
            "model": "pangram-4",
        })
        self.assertEqual(mock_post.call_args.kwargs["headers"]["x-api-key"], "test-key")
        self.assertEqual(result, bulk_response)

    def test_submit_bulk_with_items(self):
        pangram_client = Pangram(api_key="test-key")
        bulk_response = {
            "bulk_id": "blk_123",
            "status": "queued",
            "total_items": 2,
            "accepted_items": [
                {"index": 0, "id": "row-1", "task_id": "task-1"},
            ],
            "failed_items": [
                {"index": 1, "id": "row-2", "task_id": None, "stage": "STAGE_FAILED", "error": "invalid text"},
            ],
        }

        with patch(
            "pangram.text_classifier.requests.post",
            return_value=MockResponse(status_code=202, json_data=bulk_response),
        ) as mock_post:
            result = pangram_client.submit_bulk(
                model="pangram-4",
                items=[
                    {"id": "row-1", "text": "hello"},
                    {"id": "row-2", "text": ""},
                ],
            )

        self.assertEqual(mock_post.call_args.kwargs["json"], {
            "items": [
                {"id": "row-1", "text": "hello"},
                {"id": "row-2", "text": ""},
            ],
            "model": "pangram-4",
        })
        self.assertNotIn("model", mock_post.call_args.kwargs["json"]["items"][0])
        self.assertEqual(result, bulk_response)

    def test_submit_bulk_requires_exactly_one_payload_shape(self):
        pangram_client = Pangram(api_key="test-key")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            pangram_client.submit_bulk(model="default")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            pangram_client.submit_bulk(
                model="default",
                text=["hello"],
                items=[{"text": "hello"}],
            )

    def test_submit_bulk_wraps_request_errors_with_retry_key(self):
        pangram_client = Pangram(api_key="test-key")
        with patch(
            "pangram.text_classifier.requests.post",
            side_effect=requests.exceptions.Timeout("timed out"),
        ):
            with self.assertRaisesRegex(
                ValueError,
                r"submitting bulk job \(retry safely by resubmitting with "
                r"idempotency_key='my-stable-key'\): timed out",
            ):
                pangram_client.submit_bulk(
                    model="default",
                    text=["hello"],
                    idempotency_key="my-stable-key",
                )

    def test_submit_bulk_generates_unique_idempotency_key_per_call(self):
        pangram_client = Pangram(api_key="test-key")
        bulk_response = {
            "bulk_id": "blk_123",
            "status": "queued",
            "total_items": 1,
            "accepted_items": [{"index": 0, "id": None, "task_id": "task-1"}],
            "failed_items": [],
        }

        with patch(
            "pangram.text_classifier.requests.post",
            return_value=MockResponse(status_code=202, json_data=bulk_response),
        ) as mock_post:
            pangram_client.submit_bulk(model="default", text=["hello"])
            pangram_client.submit_bulk(model="default", text=["hello"])

        keys = [
            call.kwargs["headers"]["Idempotency-Key"]
            for call in mock_post.call_args_list
        ]
        self.assertTrue(all(key.startswith("pangram-sdk-") for key in keys))
        self.assertEqual(len(set(keys)), 2)

    def test_submit_bulk_sends_explicit_idempotency_key(self):
        pangram_client = Pangram(api_key="test-key")
        bulk_response = {
            "bulk_id": "blk_123",
            "status": "queued",
            "total_items": 1,
            "accepted_items": [{"index": 0, "id": None, "task_id": "task-1"}],
            "failed_items": [],
        }

        with patch(
            "pangram.text_classifier.requests.post",
            return_value=MockResponse(status_code=202, json_data=bulk_response),
        ) as mock_post:
            pangram_client.submit_bulk(
                model="default",
                text=["hello"],
                idempotency_key="my-stable-key",
            )

        headers = mock_post.call_args.kwargs["headers"]
        self.assertEqual(headers["Idempotency-Key"], "my-stable-key")
        self.assertEqual(headers["x-api-key"], "test-key")

    def test_submit_bulk_rejects_invalid_idempotency_key(self):
        pangram_client = Pangram(api_key="test-key")
        for invalid_key in ["", "x" * 256]:
            with self.assertRaisesRegex(ValueError, "idempotency_key"):
                pangram_client.submit_bulk(
                    model="default",
                    text=["hello"],
                    idempotency_key=invalid_key,
                )

    def test_get_bulk_status(self):
        pangram_client = Pangram(api_key="test-key")
        status_response = {
            "bulk_id": "blk_123",
            "status": "running",
            "total_items": 2,
            "accepted": 2,
            "succeeded": 1,
            "failed": 0,
            "created_at": "1760000000.0",
            "completed_at": None,
        }

        with patch(
            "pangram.text_classifier.requests.get",
            return_value=MockResponse(json_data=status_response),
        ) as mock_get:
            result = pangram_client.get_bulk_status("blk_123")

        self.assertEqual(mock_get.call_args.args[0], f"{API_ENDPOINT}/bulk/blk_123")
        self.assertEqual(mock_get.call_args.kwargs["headers"]["x-api-key"], "test-key")
        self.assertEqual(result, status_response)

    def test_get_bulk_items_and_results_page_use_pagination_params(self):
        pangram_client = Pangram(api_key="test-key")
        items_response = {
            "bulk_id": "blk_123",
            "offset": 10,
            "limit": 25,
            "total_items": 100,
            "items": [],
        }
        results_response = {
            "bulk_id": "blk_123",
            "offset": 10,
            "limit": 25,
            "total_items": 100,
            "items": [],
            "failed_items": [],
        }

        with patch(
            "pangram.text_classifier.requests.get",
            side_effect=[
                MockResponse(json_data=items_response),
                MockResponse(json_data=results_response),
            ],
        ) as mock_get:
            items = pangram_client.get_bulk_items("blk_123", offset=10, limit=25)
            results = pangram_client.get_bulk_results_page("blk_123", offset=10, limit=25)

        self.assertEqual(mock_get.call_args_list[0].args[0], f"{API_ENDPOINT}/bulk/blk_123/items")
        self.assertEqual(mock_get.call_args_list[0].kwargs["params"], {"offset": 10, "limit": 25})
        self.assertEqual(mock_get.call_args_list[1].args[0], f"{API_ENDPOINT}/bulk/blk_123/results")
        self.assertEqual(mock_get.call_args_list[1].kwargs["params"], {"offset": 10, "limit": 25})
        self.assertEqual(items, items_response)
        self.assertEqual(results, results_response)

    def test_get_bulk_results_page_preserves_pangram_4_window_fields(self):
        pangram_client = Pangram(api_key="test-key")
        results_response = {
            "bulk_id": "blk_123",
            "offset": 0,
            "limit": 100,
            "total_items": 1,
            "items": [
                {
                    "index": 0,
                    "id": "row-1",
                    "task_id": "task-1",
                    "stage": "STAGE_SUCCESS",
                    "error": None,
                    "result": {
                        "stage": "STAGE_SUCCESS",
                        "text": "Human-written text.",
                        "version": "4.0",
                        "headline": "Human Written",
                        "prediction": "We believe this text is human-written.",
                        "prediction_short": "Human",
                        "fraction_ai": 0.0,
                        "fraction_ai_assisted": 0.0,
                        "fraction_human": 1.0,
                        "num_ai_segments": 0,
                        "num_ai_assisted_segments": 0,
                        "num_human_segments": 1,
                        "windows": [
                            {
                                "text": "Human-written text.",
                                "label": "Human Written",
                                "ai_assistance_score": 0.0,
                                "confidence": "High",
                                "start_index": 0,
                                "end_index": 19,
                                "word_count": 2,
                                "token_length": 4,
                                "is_humanized": False,
                                "humanizer_score": 0.0,
                            }
                        ],
                    },
                }
            ],
            "failed_items": [],
        }

        with patch(
            "pangram.text_classifier.requests.get",
            return_value=MockResponse(json_data=results_response),
        ):
            result = pangram_client.get_bulk_results_page("blk_123")

        window = result["items"][0]["result"]["windows"][0]
        self.assertIs(window["is_humanized"], False)
        self.assertEqual(window["humanizer_score"], 0.0)

    def test_get_bulk_results_fetches_all_pages(self):
        pangram_client = Pangram(api_key="test-key")
        first_page = {
            "bulk_id": "blk_123",
            "offset": 0,
            "limit": 2,
            "total_items": 3,
            "items": [
                {"index": 0, "id": "row-1", "task_id": "task-1", "stage": "STAGE_SUCCESS", "result": {}},
            ],
            "failed_items": [
                {"index": 1, "id": "row-2", "task_id": None, "stage": "STAGE_FAILED", "error": "invalid text"},
            ],
        }
        second_page = {
            "bulk_id": "blk_123",
            "offset": 2,
            "limit": 2,
            "total_items": 3,
            "items": [
                {"index": 2, "id": "row-3", "task_id": "task-3", "stage": "STAGE_SUCCESS", "result": {}},
            ],
            "failed_items": [],
        }

        with patch.object(
            PangramText,
            "get_bulk_results_page",
            side_effect=[first_page, second_page],
        ) as mock_page:
            results = pangram_client.get_bulk_results("blk_123", page_size=2)

        self.assertEqual(mock_page.call_args_list[0].kwargs, {"offset": 0, "limit": 2})
        self.assertEqual(mock_page.call_args_list[1].kwargs, {"offset": 2, "limit": 2})
        self.assertEqual(results["bulk_id"], "blk_123")
        self.assertEqual(results["total_items"], 3)
        self.assertEqual([item["index"] for item in results["items"]], [0, 2])
        self.assertEqual([item["index"] for item in results["failed_items"]], [1])

    def test_get_bulk_results_rejects_invalid_page_size(self):
        pangram_client = Pangram(api_key="test-key")
        with self.assertRaisesRegex(ValueError, "page_size must be between"):
            pangram_client.get_bulk_results("blk_123", page_size=0)

    def test_wait_for_bulk_returns_terminal_status(self):
        pangram_client = Pangram(api_key="test-key")
        with patch.object(
            PangramText,
            "_fetch_bulk_status",
            side_effect=[
                {"bulk_id": "blk_123", "status": "queued"},
                {"bulk_id": "blk_123", "status": "running"},
                {"bulk_id": "blk_123", "status": "partial"},
            ],
        ) as mock_status, patch("pangram.text_classifier.time.sleep") as mock_sleep:
            result = pangram_client.wait_for_bulk("blk_123", timeout=10, poll_interval=0)

        self.assertEqual(result["status"], "partial")
        self.assertEqual(mock_status.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_called_with(MIN_POLL_INTERVAL_SECONDS)

    def test_wait_for_bulk_uses_remaining_deadline_for_poll_request_timeout(self):
        pangram_client = Pangram(api_key="test-key")
        terminal_response = {
            "bulk_id": "blk_123",
            "status": "succeeded",
            "total_items": 1,
            "accepted": 1,
            "succeeded": 1,
            "failed": 0,
            "created_at": "1760000000.0",
            "completed_at": "1760000001.0",
        }

        with patch(
            "pangram.text_classifier.requests.get",
            return_value=MockResponse(json_data=terminal_response),
        ) as mock_get:
            result = pangram_client.wait_for_bulk("blk_123", timeout=1, poll_interval=0)

        self.assertEqual(result["status"], "succeeded")
        self.assertLessEqual(mock_get.call_args.kwargs["timeout"], 1.0)

    def test_wait_for_bulk_retries_poll_request_errors_before_deadline(self):
        pangram_client = Pangram(api_key="test-key")
        with patch.object(
            PangramText,
            "_fetch_bulk_status",
            side_effect=[
                requests.exceptions.ConnectionError("connection dropped"),
                {"bulk_id": "blk_123", "status": "succeeded"},
            ],
        ) as mock_status, patch("pangram.text_classifier.time.sleep") as mock_sleep:
            result = pangram_client.wait_for_bulk("blk_123", timeout=10, poll_interval=0)

        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(mock_status.call_count, 2)
        mock_sleep.assert_called_once_with(MIN_POLL_INTERVAL_SECONDS)

    def test_wait_for_bulk_rejects_invalid_timeout(self):
        pangram_client = Pangram(api_key="test-key")
        with self.assertRaisesRegex(ValueError, "timeout must be greater than 0"):
            pangram_client.wait_for_bulk("blk_123", timeout=0)

class TestDashboard(unittest.TestCase):
    def test_dashboard(self):
        text = "hello!"
        pangram_client = Pangram(api_key="test-key")
        success_response = {
            "stage": "STAGE_SUCCESS",
            "text": text,
            "version": "4.0",
            "headline": "Human Written",
            "prediction": "We believe this text is human-written.",
            "prediction_short": "Human",
            "fraction_ai": 0.0,
            "fraction_ai_assisted": 0.0,
            "fraction_human": 1.0,
            "num_ai_segments": 0,
            "num_ai_assisted_segments": 0,
            "num_human_segments": 1,
            "dashboard_link": "https://www.pangram.com/history/query-1",
            "windows": [],
        }

        with patch(
            "pangram.text_classifier.requests.post",
            return_value=MockResponse(json_data={"task_id": "task-1"}),
        ) as mock_post, patch(
            "pangram.text_classifier.requests.get",
            side_effect=[
                MockResponse(json_data={"task_id": "task-1", "stage": "STAGE_PREPROCESSING"}),
                MockResponse(json_data=success_response),
            ],
        ), patch("pangram.text_classifier.time.sleep") as mock_sleep:
            result = pangram_client.predict_with_dashboard_link(
                text,
                model="pangram-4",
                timeout=1,
                poll_interval=0,
            )

        self.assertEqual(mock_post.call_args.args[0], f"{API_ENDPOINT}/task")
        self.assertEqual(mock_post.call_args.kwargs["json"], {
            "text": text,
            "model": "pangram-4",
            "public_dashboard_link": True,
        })
        self.assertLessEqual(mock_post.call_args.kwargs["timeout"], 1.0)
        mock_sleep.assert_called_once_with(MIN_POLL_INTERVAL_SECONDS)
        self.assertEqual(result, success_response)

class TestFileUpload(unittest.TestCase):
    def _write_test_file(self, directory, name):
        path = os.path.join(directory, name)
        with open(path, "wb") as file_obj:
            file_obj.write(b"test file contents")
        return path

    def test_predict_file_uploads_multipart_file(self):
        pangram_client = Pangram(api_key="test-key")
        upload_response = [
            {"dashboard_link": "https://www.pangram.com/history/query-1"}
        ]

        with tempfile.TemporaryDirectory() as directory:
            file_path = self._write_test_file(directory, "document.docx")
            with patch(
                "pangram.text_classifier.requests.post",
                return_value=MockResponse(json_data=upload_response),
            ) as mock_post:
                result = pangram_client.predict_file(
                    file_path,
                    public_dashboard_link=True,
                    timeout=12,
                )

        self.assertEqual(mock_post.call_args.args[0], FILE_UPLOAD_API_ENDPOINT)
        self.assertEqual(mock_post.call_args.kwargs["data"], {"public_dashboard_link": "true"})
        self.assertEqual(mock_post.call_args.kwargs["headers"], {"x-api-key": "test-key"})
        self.assertEqual(mock_post.call_args.kwargs["timeout"], 12)
        files = mock_post.call_args.kwargs["files"]
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0][0], "files")
        self.assertEqual(files[0][1][0], "document.docx")
        self.assertTrue(files[0][1][1].closed)
        self.assertEqual(result, upload_response[0])

    def test_predict_files_repeats_files_form_field(self):
        pangram_client = Pangram(api_key="test-key")
        upload_response = [
            {"dashboard_link": "https://www.pangram.com/history/query-1"},
            {"dashboard_link": "https://www.pangram.com/history/query-2"},
        ]

        with tempfile.TemporaryDirectory() as directory:
            first_path = self._write_test_file(directory, "first.pdf")
            second_path = self._write_test_file(directory, "second.rtf")
            with patch(
                "pangram.text_classifier.requests.post",
                return_value=MockResponse(json_data=upload_response),
            ) as mock_post:
                result = pangram_client.predict_files([first_path, second_path])

        self.assertEqual(mock_post.call_args.kwargs["data"], {"public_dashboard_link": "false"})
        files = mock_post.call_args.kwargs["files"]
        self.assertEqual([file_item[0] for file_item in files], ["files", "files"])
        self.assertEqual([file_item[1][0] for file_item in files], ["first.pdf", "second.rtf"])
        self.assertEqual(result, upload_response)

    def test_predict_files_requires_at_least_one_file(self):
        pangram_client = Pangram(api_key="test-key")
        with self.assertRaisesRegex(ValueError, "at least one file"):
            pangram_client.predict_files([])

    def test_predict_files_rejects_invalid_timeout(self):
        pangram_client = Pangram(api_key="test-key")
        with tempfile.TemporaryDirectory() as directory:
            file_path = self._write_test_file(directory, "document.docx")
            with self.assertRaisesRegex(ValueError, "timeout must be greater than 0"):
                pangram_client.predict_file(file_path, timeout=0)

    def test_predict_files_wraps_request_errors(self):
        pangram_client = Pangram(api_key="test-key")
        with tempfile.TemporaryDirectory() as directory:
            file_path = self._write_test_file(directory, "document.docx")
            with patch(
                "pangram.text_classifier.requests.post",
                side_effect=requests.exceptions.Timeout("timed out"),
            ):
                with self.assertRaisesRegex(ValueError, "uploading files: timed out"):
                    pangram_client.predict_file(file_path)

    def test_predict_files_rejects_invalid_response_shape(self):
        pangram_client = Pangram(api_key="test-key")
        with tempfile.TemporaryDirectory() as directory:
            file_path = self._write_test_file(directory, "document.docx")
            with patch(
                "pangram.text_classifier.requests.post",
                return_value=MockResponse(json_data={"unexpected": "shape"}),
            ):
                with self.assertRaisesRegex(ValueError, "invalid file upload response"):
                    pangram_client.predict_file(file_path)

class TestPlagiarism(unittest.TestCase):
    @unittest.skipUnless(os.getenv('PANGRAM_API_KEY'), "requires PANGRAM_API_KEY")
    def test_plagiarism(self):
        text = "hello!"
        pangram_client = Pangram()
        result = pangram_client.check_plagiarism(text)
        self.assertIn('plagiarism_detected', result)
        self.assertIn('plagiarized_content', result)
        self.assertIn('total_sentences', result)
        self.assertIn('plagiarized_sentences', result)
        self.assertIn('percent_plagiarized', result)

class TestPangramText(unittest.TestCase):
    def test_predict(self):
        """
        Ensure legacy syntax using PangramText
        """
        pangram_client = PangramText(api_key="test-key")
        text = "I recently had the pleasure of visiting OpenAI. As an AI language model, I cannot actually visit places."
        with patch.object(PangramText, "predict", return_value={"text": text}):
            result = pangram_client.predict(text, model="default")
        self.assertEqual(result['text'], text)

if __name__ == '__main__':
    unittest.main()
