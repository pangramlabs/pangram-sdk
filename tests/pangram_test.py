import unittest
from pangram import Pangram, PangramText
import os


class TestPredict(unittest.TestCase):
    def test_predict(self):
        pangram_client = Pangram()
        text = "I recently had the pleasure of visiting OpenAI. As an AI language model, I cannot actually visit places."
        result = pangram_client.predict(text)
        self.assertEqual(result['text'], text)

class TestBatchPredict(unittest.TestCase):
    def test_batch_predict(self):
        text1 = "I recently had the pleasure of visiting OpenAI. As an AI language model, I cannot actually visit places."
        text2 = "i'm a human"
        text_batch = [text1, text2]
        pangram_client = Pangram()
        results = pangram_client.batch_predict(text_batch)
        self.assertEqual(len(results), len(text_batch))

class TestSlidingWindow(unittest.TestCase):
    def test_sliding_window(self):
        text = "hello!"
        pangram_client = Pangram()
        result = pangram_client.predict_sliding_window(text)
        self.assertEqual(result['text'], text)
        self.assertIn('windows', result)

class TestDashboard(unittest.TestCase):
    def test_dashboard(self):
        text = "hello!"
        pangram_client = Pangram()
        result = pangram_client.predict_with_dashboard_link(text)
        self.assertEqual(result['text'], text)
        self.assertIn('dashboard_link', result)

class TestPlagiarism(unittest.TestCase):
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
        api_key = os.getenv('PANGRAM_API_KEY')
        pangram_client = PangramText(api_key=api_key)
        text = "I recently had the pleasure of visiting OpenAI. As an AI language model, I cannot actually visit places."
        result = pangram_client.predict(text)
        self.assertEqual(result['text'], text)

if __name__ == '__main__':
    unittest.main()
