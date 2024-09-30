import requests
import os
from typing import List

SOURCE_VERSION = "python_sdk_0.1.5"

API_ENDPOINT = 'https://text.api.pangramlabs.com'
BATCH_API_ENDPOINT = 'https://text-batch.api.pangramlabs.com'
SLIDING_WINDOW_API_ENDPOINT = 'https://text-sliding.api.pangramlabs.com'
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
        }
        response = requests.post(API_ENDPOINT, json=input_json, headers=headers, timeout=90)
        if response.status_code != 200:
            raise ValueError(f"Error returned by API: [{response.status_code}] {response.text}")
        response_json = response.json()
        if "error" in response_json:
            raise ValueError(f"Error returned by API: {response_json['error']}")
        return response_json


    def batch_predict(self, text_batch: List[str]):
        """
        Classify a batch of text as AI- or human-written.

        This method sends a batch of text to the Pangram Text API and returns the classification results.

        :param text_batch: A list of strings to be classified.
        :type text_batch: List[str]
        :return: A list of classification results from the API for each text in the batch.
        :rtype: List[dict]
        """
        if len(text_batch) > self.max_batch_size:
            raise ValueError(f"Maximum batch size is {self.max_batch_size}.")
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
        }
        input_json = {
            "text": text_batch,
            "source": SOURCE_VERSION,
        }
        response = requests.post(BATCH_API_ENDPOINT, json=input_json, headers=headers, timeout=90)
        if response.status_code != 200:
            raise ValueError(f"Error returned by API: [{response.status_code}] {response.text}")
        response_json = response.json()
        if "error" in response_json:
            raise ValueError(f"Error returned by API: {response_json['error']}")
        if "responses" not in response_json:
            raise ValueError(f"Failed to retrieve responses: {response_json}")
        return response_json["responses"]

    def predict_sliding_window(self, text: str):
        """
        Classify a long document using a sliding window to iterate across the full document.
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
        }
        response = requests.post(SLIDING_WINDOW_API_ENDPOINT, json=input_json, headers=headers, timeout=90)
        if response.status_code != 200:
            raise ValueError(f"Error returned by API: [{response.status_code}] {response.text}")
        response_json = response.json()
        if "error" in response_json:
            raise ValueError(f"Error returned by API: {response_json['error']}")
        return response_json
