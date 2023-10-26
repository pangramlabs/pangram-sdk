import unittest
from checkforai import TextClassifier
import aiounittest


class TestCheckForAI(unittest.TestCase):
    def test_predict(self):
        text = "This is a test text"
        classifier = TextClassifier()
        result = classifier.predict(text)
        self.assertIn('likelihood', result)
        print(result)

class TestCheckForAIAsync(aiounittest.AsyncTestCase):
    async def test_predict_async(self):
        text = "This is a test text"
        classifier = TextClassifier()
        result = await classifier.predict_async(text)
        self.assertIn('likelihood', result)
        print(result)


if __name__ == '__main__':
    unittest.main()
