import unittest
from pangram import Pangram, PangramText
from pangram.text_classifier import API_ENDPOINT
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

        with patch(
            "pangram.text_classifier.requests.post",
            return_value=MockResponse(json_data={"task_id": "task-1"}),
        ) as mock_post, patch(
            "pangram.text_classifier.requests.get",
            side_effect=[
                MockResponse(json_data={"task_id": "task-1", "stage": "STAGE_PREPROCESSING"}),
                MockResponse(json_data={
                    "task_id": "task-1",
                    "stage": "STAGE_SUCCESS",
                    "text": text,
                    "version": "3.1",
                    "headline": "AI Detected",
                    "prediction": "We believe this is mixed content",
                    "prediction_short": "Mixed",
                    "fraction_ai": 0.2,
                    "fraction_ai_assisted": 0.3,
                    "fraction_human": 0.5,
                    "fraction_mixed": 0.3,
                    "avg_ai_likelihood": 0.4,
                    "fraction_breakdown": {
                        "ai": {"high-confidence": 0.2},
                        "ai-assisted": {"lightly": 0.1, "moderately": 0.2},
                        "human": {"high-confidence": 0.5},
                    },
                    "num_ai_segments": 1,
                    "num_ai_assisted_segments": 2,
                    "num_human_segments": 3,
                    "window_indices": [[0, 45]],
                    "windows": [
                        {
                            "text": "I recently had the pleasure of visiting OpenAI.",
                            "ai_likelihood": 0.92,
                            "label": "AI-Generated",
                            "editlens": {"prediction_text": "AI-Generated"},
                            "confidence": "High",
                            "start_index": 0,
                            "end_index": 45,
                            "word_count": 8,
                            "token_length": 10,
                        }
                    ],
                }),
            ],
        ):
            result = pangram_client.predict(text, poll_interval=0)

        self.assertEqual(mock_post.call_args.args[0], f"{API_ENDPOINT}/task")
        self.assertEqual(mock_post.call_args.kwargs["json"], {"text": text})
        self.assertEqual(mock_post.call_args.kwargs["headers"]["x-api-key"], "test-key")
        self.assertEqual(result['text'], text)
        self.assertEqual(result["task_id"], "task-1")
        self.assertEqual(result["stage"], "STAGE_SUCCESS")
        self.assertEqual(result["version"], "3.1")
        self.assertEqual(result["prediction_short"], "Mixed")
        self.assertEqual(result["num_ai_segments"], 1)
        self.assertEqual(result["fraction_mixed"], 0.3)
        self.assertEqual(result["avg_ai_likelihood"], 0.4)
        self.assertEqual(result["fraction_breakdown"]["ai-assisted"], {"lightly": 0.1, "moderately": 0.2})
        self.assertEqual(result["window_indices"], [[0, 45]])
        self.assertEqual(result["windows"][0]["ai_assistance_score"], 0.92)
        self.assertEqual(result["windows"][0]["label"], "AI-Generated")
        self.assertEqual(result["windows"][0]["ai_likelihood"], 0.92)
        self.assertEqual(result["windows"][0]["editlens"], {"prediction_text": "AI-Generated"})

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

class TestBatchPredict(unittest.TestCase):
    def test_batch_predict(self):
        text1 = "I recently had the pleasure of visiting OpenAI. As an AI language model, I cannot actually visit places."
        text2 = "i'm a human"
        text_batch = [text1, text2]
        pangram_client = Pangram(api_key="test-key")
        with patch.object(PangramText, "predict", side_effect=[{"text": text1}, {"text": text2}]):
            results = pangram_client.batch_predict(text_batch)
        self.assertEqual(len(results), len(text_batch))

class TestSlidingWindow(unittest.TestCase):
    @unittest.skipUnless(os.getenv('PANGRAM_API_KEY'), "requires PANGRAM_API_KEY")
    def test_sliding_window(self):
        text = "hello!"
        pangram_client = Pangram()
        result = pangram_client.predict_sliding_window(text)
        self.assertEqual(result['text'], text)
        self.assertIn('windows', result)

class TestDashboard(unittest.TestCase):
    def test_dashboard(self):
        text = "hello!"
        pangram_client = Pangram(api_key="test-key")
        with patch.object(PangramText, "predict", return_value={"text": text}) as mock_predict:
            result = pangram_client.predict_with_dashboard_link(text)
        self.assertEqual(result['text'], text)
        mock_predict.assert_called_once_with(text, public_dashboard_link=True)

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
