import unittest
from checkforai import TextClassifier
import aiounittest


class TestCheckForAI(unittest.TestCase):
    def test_predict(self):
        text = "I recently had the pleasure of visiting OpenAI. As an AI language model, I cannot actually visit places."
        classifier = TextClassifier()
        result = classifier.predict(text)
        self.assertIn('likelihood', result)
        print(result)

class TestCheckForAIAsync(aiounittest.AsyncTestCase):
    async def test_predict_async(self):
        text = "i'm a human"
        classifier = TextClassifier()
        result = await classifier.predict_async(text)
        self.assertIn('likelihood', result)
        print(result)


if __name__ == '__main__':
    unittest.main()
