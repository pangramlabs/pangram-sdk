import requests
import os
from typing import List


API_ENDPOINT = 'https://api.checkfor.ai/v1/classify/text'
BATCH_API_ENDPOINT = 'https://api.checkfor.ai/v1/classify/text/batch'


class TextClassifier:
    def __init__(self, api_key: str = None) -> None:
        """
        A classifier for text inputs using the checkfor.ai API.

        This class provides synchronous and asynchronous methods to classify text by making API requests.

        :param api_key: The API key for the checkfor.ai service. If not provided, the environment variable CHECKFORAI_API_KEY will be used.
        :type api_key: str, optional
        :raises ValueError: If the API key is not provided and not set in the environment.
        """
        if api_key is None:
            self.api_key = os.getenv('CHECKFORAI_API_KEY')
            if self.api_key is None:
                raise ValueError("API key is required. Set the environment variable CHECKFORAI_API_KEY or pass it as an argument.")
        else:
            self.api_key = api_key


    def predict(self, text: str, logging: bool = True):
        """
        Predict the classification of the given text.

        Sends a POST request to the Checkfor.ai API and returns the classification result.

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
            "source": "python",
            "cid": self.api_key,
            "logging": logging,
        }
        response = requests.post(API_ENDPOINT, json=input_json, headers=headers, timeout=30)
        return response.json()


    def batch_predict(self, text_batch: List[str], logging: bool = True):
        """
        Predict the classification of the given text.

        Sends a POST request to the Checkfor.ai API and returns the classification result.

        :param text_batch: A list of strings to be classified.
        :type text: List
        :return: The classification result from the API.
        :rtype: dict
        """
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
        }
        input_json = {
            "text": text_batch,
            "source": "python_batch",
            "cid": self.api_key,
            "logging": logging,
        }
        response = requests.post(BATCH_API_ENDPOINT, json=input_json, headers=headers, timeout=30)
        return response.json()["responses"]
