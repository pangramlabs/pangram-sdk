import unittest
from pangram import PangramText

class TestPredict(unittest.TestCase):
    def test_predict(self):
        text = "I recently had the pleasure of visiting OpenAI. As an AI language model, I cannot actually visit places."
        classifier = PangramText()
        result = classifier.predict(text)
        self.assertEqual(result['text'], text)
        self.assertLess(result['ai_likelihood'], 1.0)
        self.assertGreater(result['ai_likelihood'], 0.0)
        print(result)

class TestBatchPredict(unittest.TestCase):
    def test_batch_predict(self):
        text1 = "I recently had the pleasure of visiting OpenAI. As an AI language model, I cannot actually visit places."
        text2 = "i'm a human"
        text_batch = [text1, text2]
        classifier = PangramText()
        results = classifier.batch_predict(text_batch)
        self.assertEqual(len(results), len(text_batch))
        self.assertEqual(results[0]["text"], text_batch[0])
        self.assertLess(results[0]["ai_likelihood"], 1)
        print(results)


if __name__ == '__main__':
    unittest.main()
