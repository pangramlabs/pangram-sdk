import unittest
import requests
from pangram import Pangram, PangramText
from pangram.text_classifier import API_ENDPOINT, MIN_POLL_INTERVAL_SECONDS
import os
from unittest.mock import patch


class MockResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        return self._json_data


class TestPredict(unittest.TestCase):
    def test_predict(self):
        text = "I recently had the pleasure of visiting OpenAI. As an AI language model, I cannot actually visit places."
        pangram_client = Pangram(api_key="test-key")
        success_response = {
            "stage": "STAGE_SUCCESS",
            "text": text,
            "version": "3.1",
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
            result = pangram_client.predict(text, poll_interval=0)

        self.assertEqual(mock_post.call_args.args[0], f"{API_ENDPOINT}/task")
        self.assertEqual(mock_post.call_args.kwargs["json"], {"text": text, "public_dashboard_link": False})
        self.assertEqual(mock_post.call_args.kwargs["headers"]["x-api-key"], "test-key")
        mock_sleep.assert_called_once_with(MIN_POLL_INTERVAL_SECONDS)
        self.assertEqual(result, success_response)

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
                pangram_client.predict("hello", poll_interval=0)

    def test_predict_rejects_invalid_timeout(self):
        pangram_client = Pangram(api_key="test-key")
        with self.assertRaisesRegex(ValueError, "timeout must be greater than 0"):
            pangram_client.predict("hello", timeout=0)

    def test_predict_wraps_submit_request_errors(self):
        pangram_client = Pangram(api_key="test-key")
        with patch(
            "pangram.text_classifier.requests.post",
            side_effect=requests.exceptions.Timeout("timed out"),
        ):
            with self.assertRaisesRegex(ValueError, "submitting prediction task: timed out"):
                pangram_client.predict("hello")

    def test_predict_retries_poll_request_errors(self):
        pangram_client = Pangram(api_key="test-key")
        success_response = {
            "stage": "STAGE_SUCCESS",
            "text": "hello",
            "prediction_short": "Human",
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
            result = pangram_client.predict("hello", poll_interval=0)

        mock_sleep.assert_called_once_with(MIN_POLL_INTERVAL_SECONDS)
        self.assertEqual(result, success_response)

    def test_predict_short_forwards_to_predict(self):
        text = "hello!"
        pangram_client = Pangram(api_key="test-key")
        with patch.object(PangramText, "predict", return_value={"text": text}) as mock_predict:
            with self.assertWarnsRegex(DeprecationWarning, "predict_short"):
                result = pangram_client.predict_short(text)

        mock_predict.assert_called_once_with(text)
        self.assertEqual(result, {"text": text})

class TestBatchPredict(unittest.TestCase):
    def test_batch_predict(self):
        text1 = "I recently had the pleasure of visiting OpenAI. As an AI language model, I cannot actually visit places."
        text2 = "i'm a human"
        text_batch = [text1, text2]
        pangram_client = Pangram(api_key="test-key")
        with patch.object(PangramText, "predict", side_effect=[{"text": text1}, {"text": text2}]):
            with self.assertWarnsRegex(DeprecationWarning, "batch_predict"):
                results = pangram_client.batch_predict(text_batch)
        self.assertEqual(len(results), len(text_batch))

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
            result = pangram_client.submit_bulk(text=["hello", "world"])

        self.assertEqual(mock_post.call_args.args[0], f"{API_ENDPOINT}/bulk")
        self.assertEqual(mock_post.call_args.kwargs["json"], {"text": ["hello", "world"]})
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
            result = pangram_client.submit_bulk(items=[
                {"id": "row-1", "text": "hello"},
                {"id": "row-2", "text": ""},
            ])

        self.assertEqual(mock_post.call_args.kwargs["json"], {
            "items": [
                {"id": "row-1", "text": "hello"},
                {"id": "row-2", "text": ""},
            ]
        })
        self.assertEqual(result, bulk_response)

    def test_submit_bulk_requires_exactly_one_payload_shape(self):
        pangram_client = Pangram(api_key="test-key")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            pangram_client.submit_bulk()
        with self.assertRaisesRegex(ValueError, "exactly one"):
            pangram_client.submit_bulk(text=["hello"], items=[{"text": "hello"}])

    def test_submit_bulk_wraps_request_errors(self):
        pangram_client = Pangram(api_key="test-key")
        with patch(
            "pangram.text_classifier.requests.post",
            side_effect=requests.exceptions.Timeout("timed out"),
        ):
            with self.assertRaisesRegex(ValueError, "submitting bulk job: timed out"):
                pangram_client.submit_bulk(text=["hello"])

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

    def test_get_bulk_items_and_results_use_pagination_params(self):
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
            results = pangram_client.get_bulk_results("blk_123", offset=10, limit=25)

        self.assertEqual(mock_get.call_args_list[0].args[0], f"{API_ENDPOINT}/bulk/blk_123/items")
        self.assertEqual(mock_get.call_args_list[0].kwargs["params"], {"offset": 10, "limit": 25})
        self.assertEqual(mock_get.call_args_list[1].args[0], f"{API_ENDPOINT}/bulk/blk_123/results")
        self.assertEqual(mock_get.call_args_list[1].kwargs["params"], {"offset": 10, "limit": 25})
        self.assertEqual(items, items_response)
        self.assertEqual(results, results_response)

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
            "dashboard_link": "https://www.pangram.com/history/query-1",
            "windows": [],
        }

        with patch(
            "pangram.text_classifier.requests.post",
            return_value=MockResponse(json_data={"task_id": "task-1"}),
        ) as mock_post, patch(
            "pangram.text_classifier.requests.get",
            return_value=MockResponse(json_data=success_response),
        ):
            result = pangram_client.predict_with_dashboard_link(text)

        self.assertEqual(mock_post.call_args.args[0], f"{API_ENDPOINT}/task")
        self.assertEqual(mock_post.call_args.kwargs["json"], {"text": text, "public_dashboard_link": True})
        self.assertEqual(result, success_response)

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
            result = pangram_client.predict(text)
        self.assertEqual(result['text'], text)

if __name__ == '__main__':
    unittest.main()
