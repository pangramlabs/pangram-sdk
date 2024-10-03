import unittest
from pangram import PangramText
import os


class TestPredict(unittest.TestCase):
    def test_predict(self):
        pangram_client = Pangram()
        text = "I recently had the pleasure of visiting OpenAI. As an AI language model, I cannot actually visit places."
        result = pangram_client.predict(text)
        self.assertEqual(result['text'], text)
        self.assertLess(result['ai_likelihood'], 1.0)
        self.assertGreater(result['ai_likelihood'], 0.0)
        print(result)

class TestBatchPredict(unittest.TestCase):
    def test_batch_predict(self):
        text1 = "I recently had the pleasure of visiting OpenAI. As an AI language model, I cannot actually visit places."
        text2 = "i'm a human"
        text_batch = [text1, text2]
        pangram_client = Pangram()
        results = pangram_client.batch_predict(text_batch)
        self.assertEqual(len(results), len(text_batch))
        self.assertEqual(results[0]["text"], text_batch[0])
        self.assertLess(results[0]["ai_likelihood"], 1)
        print(results)

class TestSlidingWindow(unittest.TestCase):
    def test_sliding_window(self):
        text = "hello!"
        pangram_client = Pangram()
        result = pangram_client.predict_sliding_window(text)
        print(result)

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
        self.assertLess(result['ai_likelihood'], 1.0)
        self.assertGreater(result['ai_likelihood'], 0.0)
        print(result)

if __name__ == '__main__':
    unittest.main()
