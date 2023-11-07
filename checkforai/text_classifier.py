import requests
import os
import aiohttp

API_URL = 'https://api.checkfor.ai/inference'


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


    def predict(self, text: str):
        """
        Synchronously predict the classification of the given text.

        Sends a POST request to the checkfor.ai API and returns the classification result.

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
            "input": text,
        }
        response = requests.post(API_URL, json=input_json, headers=headers, timeout=10)
        return response.json()


    async def predict_async(self, text: str):
        """
        Asynchronously predict the classification of the given text.

        This function sends a POST request to the checkfor.ai API.

        :param text: The text to be classified.
        :type text: str
        :return: The classification result from the API as a JSON object.
        :rtype: dict
        """
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
        }
        input_json = {
            "input": text,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                API_URL,
                headers=headers,
                json=input_json,
            ) as response:
                return await response.json()
