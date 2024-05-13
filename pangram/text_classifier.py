import requests
import os
from typing import List

SOURCE_VERSION = "python_sdk_0.1.0"

API_ENDPOINT = 'https://text.api.pangramlabs.com'
BATCH_API_ENDPOINT = 'https://text-batch.api.pangramlabs.com'
MAX_BATCH_SIZE = 32

class PangramText:
    def __init__(self, api_key: str = None, max_batch_size = MAX_BATCH_SIZE) -> None:
        """
        A classifier for text inputs using the Pangram Labs API.

        This class provides synchronous and asynchronous methods to classify text by making API requests.

        :param api_key: Your API key for the Pangram Labs. If not provided, the environment variable PANGRAM_API_KEY will be used.
        :type api_key: str, optional
        :raises ValueError: If the API key is not provided and not set in the environment.
        """
        if api_key is None:
            self.api_key = os.getenv('PANGRAM_API_KEY')
            if self.api_key is None:
                raise ValueError("API key is required. Set the environment variable PANGRAM_API_KEY or pass it as an argument.")
        else:
            self.api_key = api_key
        self.max_batch_size = max_batch_size


    def predict(self, text: str):
        """
        Classify text as AI- or human-written.

        Sends a request to the Pangram Text API and returns the classification result.

        :param text: The text to be classified.
        :type text: str
        :return: The classification result from the API.
        :rtype: dict
        """
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
        }
        input_json = {
            "text": text,
            "source": SOURCE_VERSION,
            "cid": self.api_key,
            "logging": logging,
        }
        response = requests.post(API_ENDPOINT, json=input_json, headers=headers, timeout=90)
        return response.json()


    def batch_predict(self, text_batch: List[str]):
        """
        Classify a batch of text as AI- or human-written.

        Automatically batches the input, sends requests in batches, and yields the results as they return.

        :param text_batch: A list of strings to be classified.
        :type text_batch: List[str]
        :return: A generator yielding classification results from the API for each text in the batch.
        :rtype: Generator[dict, None, None]
        """
        for i in range(0, len(text_batch), self.max_batch_size):
            batch = text_batch[i:i + self.max_batch_size]
            results = self._individual_batch_prediction(batch)
            for result in results:
                yield result
    
    def _individual_batch_prediction(self, text_batch: List[str]):
        """
        Helper method to classify a batch of text as AI- or human-written.

        This method sends a batch of text to the Pangram Text API and returns the classification results.

        :param text_batch: A list of strings to be classified.
        :type text_batch: List[str]
        :return: A list of classification results from the API for each text in the batch.
        :rtype: List[dict]
        """
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
        }
        input_json = {
            "text": text_batch,
            "source": SOURCE_VERSION,
            "cid": self.api_key,
            "logging": logging,
        }
        response = requests.post(BATCH_API_ENDPOINT, json=input_json, headers=headers, timeout=90)
        return response.json()["responses"]
