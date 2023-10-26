import requests
import os
import aiohttp

API_URL = 'https://api.checkfor.ai/inference'


class TextClassifier:
    def __init__(self, api_key: str = None) -> None:
        if api_key is None:
            self.api_key = os.getenv('CHECKFORAI_API_KEY')
            if self.api_key is None:
                raise ValueError("API key is required. Set the environment variable CHECKFORAI_API_KEY or pass it as an argument.")
        else:
            self.api_key = api_key


    def predict(self, text: str):
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
        }
        input_json = {
            "input": text,
            "cid": "1234",
        }
        response = requests.post(API_URL, json=input_json, headers=headers, timeout=10)
        return response.json()


    async def predict_async(self, text: str):
        """
        Asynchronous function to send a POST request to the checkfor.ai API.

        Args:
            text (str): The text to be classified.

        Returns:
            dict: The response from the API as a JSON object.
        """
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
        }
        input_json = {
            "input": text,
            "cid": "1234",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                API_URL,
                headers=headers,
                json=input_json,
            ) as response:
                return await response.json()
