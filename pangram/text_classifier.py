import requests
import os
import warnings
from typing import List, Dict, Optional

SOURCE_VERSION = "python_sdk_0.1.11"

API_ENDPOINT = 'https://text.api.pangram.com/v3'
BATCH_API_ENDPOINT = 'https://text-batch.api.pangramlabs.com'
SLIDING_WINDOW_API_ENDPOINT = 'https://text-sliding.api.pangramlabs.com'
PLAGIARISM_API_ENDPOINT = 'https://plagiarism.api.pangram.com'
TEXT_EXTENDED_API_ENDPOINT = 'https://text-extended.api.pangramlabs.com'

class PangramText:
    def __init__(self, api_key: str = None) -> None:
        """
        A classifier for text inputs using the Pangram Labs API.

        :param api_key: Your API key for the Pangram Labs. If not provided, the environment variable PANGRAM_API_KEY will be used.
        :type api_key: str, optional
        :raises ValueError: If the API key is not provided and not set in the environment.
        """
        if api_key is None:
            self.api_key = os.getenv('PANGRAM_API_KEY')
        else:
            self.api_key = api_key
        if self.api_key is None:
            raise ValueError("API key is required. Set the environment variable PANGRAM_API_KEY or pass it as an argument to PangramText.")


    def predict_short(self, text: str):
        """
        Classify text as AI- or human-written using the short endpoint.

        Sends a request to the Pangram Text API and returns the classification result.

        :param text: The text to be classified.
        :type text: str
        :return: The classification result from the API, as a dict with the following fields:

                - text (str): The input text.
                - ai_likelihood (float): The classification of the text, on a scale from 0.0 (human) to 1.0 (AI).
                - prediction (str): A string representing the classification.
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


    def predict(self, text: str, public_dashboard_link: bool = False) -> Dict:
        """
        Classify text as AI-, AI-assisted, or human-written using the V3 API.

        Sends a request to the Pangram Text API V3 endpoint and returns analysis with windowed results.
        This endpoint now provides AI-assistance detection in the segment-level analysis.

        :param text: The text to be classified.
        :type text: str
        :param public_dashboard_link: Whether to include a public dashboard link in the response. Defaults to False.
        :type public_dashboard_link: bool
        :return: Pangram analysis with AI-assistance detection as a dict with the following fields:

                - text (str): The input text.
                - version (str): The API version identifier (e.g., "3.0").
                - headline (str): Classification headline summarizing the result.
                - prediction (str): Long-form prediction string describing the classification.
                - prediction_short (str): Short-form prediction string ("AI", "AI-Assisted", "Human", "Mixed").
                - fraction_ai (float): Fraction of text classified as AI-written (0.0-1.0).
                - fraction_ai_assisted (float): Fraction of text classified as AI-assisted (0.0-1.0).
                - fraction_human (float): Fraction of text classified as human-written (0.0-1.0).
                - num_ai_segments (int): Number of text segments classified as AI.
                - num_ai_assisted_segments (int): Number of text segments classified as AI-assisted.
                - num_human_segments (int): Number of text segments classified as human.
                - dashboard_link (str): A link to the dashboard page containing the full classification result. Only present when public_dashboard_link is True.
                - windows (list): List of text windows and their classifications. Each window contains:
                    - text (str): The window text.
                    - label (str): Descriptive classification label (e.g., "AI-Generated", "Moderately AI-Assisted").
                    - ai_assistance_score (float): Score detailing the level of AI assistance within the window (0.0-1.0), where 0 means no AI assistance and 1.0 means AI-generated.
                    - confidence (str): Confidence level for the classification ("High", "Medium", "Low").
                    - start_index (int): Starting character index in the original text.
                    - end_index (int): Ending character index in the original text.
                    - word_count (int): Number of words in the window.
                    - token_length (int): Token length of the window.
        :rtype: Dict
        :raises ValueError: If the API returns an error or if the response is invalid
        """
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
        }
        input_json = {
            "text": text,
            "source": SOURCE_VERSION,
            "public_dashboard_link": public_dashboard_link,
        }

        response = requests.post(API_ENDPOINT, json=input_json, headers=headers, timeout=90)
        if response.status_code != 200:
            raise ValueError(f"Error returned by API: [{response.status_code}] {response.text}")
        response_json = response.json()
        if "error" in response_json:
            raise ValueError(f"Error returned by API: {response_json['error']}")
        return response_json


    def batch_predict(self, text_batch: List[str]) -> List[Dict]:
        """
        Classify a batch of text as AI-, AI-assisted, or human-written.

        This method iterates through the batch and calls predict() for each text.

        :param text_batch: A list of strings to be classified.
        :type text_batch: List[str]
        :return: A list of classification results from the API for each text in the batch.
                 Each result is a dict with the same fields as returned by predict().
        :rtype: List[Dict]
        """
        results = []
        for text in text_batch:
            result = self.predict(text)
            results.append(result)
        return results


    def predict_sliding_window(self, text: str):
        """
        Classify a long document using a sliding window to iterate across the full document.

        .. deprecated:: 0.1.8
           This method is deprecated. Use :meth:`predict` instead for better performance. This method will be removed by April 1st, 2026. 

        :param text: The text to be classified.
        :type text: str
        :return: The classification result from the API, as a dict with the following fields:

                - text (string): The classified text.
                - ai_likelihood (float): The classification of the text, on a scale from 0.0 (human) to 1.0 (AI).
                - max_ai_likelihood (float): The maximum AI likelihood score among all windows.
                - avg_ai_likelihood (float): The average AI likelihood score among all windows.
                - prediction (string): A string representing the classification.
                - short_prediction (string): A short string representing the classification ("AI", "Human", "Mixed").
                - fraction_ai_content (float): The fraction of windows that are classified as AI.
                - windows (list): A list of windows and their individual classifications. Each object in the list is the response from a single text prediction.
        :rtype: dict
        """
        warnings.warn(
            "predict_sliding_window() is deprecated. Use predict() instead to access Pangram's latest model. This method will be removed by April 1st, 2026.",
            DeprecationWarning,
            stacklevel=2
        )
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


    def predict_with_dashboard_link(self, text: str):
        """
        Classify text as AI- or human-written.

        Sends a request to the Pangram Text API and returns the classification result, along with a
        link to a dashboard page containing the classification result.

        :param text: The text to be classified.
        :type text: str
        :return: The classification result from the API, as a dict with the following fields:

                - text (string): The classified text.
                - dashboard_link (string): A link to a dashboard page containing the classification result.
                - ai_likelihood (float): The classification of the text, on a scale from 0.0 (human) to 1.0 (AI).
                - max_ai_likelihood (float): The maximum AI likelihood score among all windows.
                - avg_ai_likelihood (float): The average AI likelihood score among all windows.
                - prediction (string): A string representing the classification.
                - short_prediction (string): A short string representing the classification ("AI", "Human", "Mixed").
                - fraction_ai_content (float): The fraction of windows that are classified as AI.
                - windows (list): A list of windows and their individual classifications. Each object in the list is the response from a single text prediction.
        :rtype: dict
        """
        return self.predict(text, public_dashboard_link=True)

    def check_plagiarism(self, text: str) -> Dict:
        """
        Check text for potential plagiarism by comparing it against a vast database of online content.

        :param text: The text to check for plagiarism.
        :type text: str
        :return: A dictionary containing the plagiarism check results, including:

                - text (str): The input text.
                - plagiarism_detected (bool): Whether plagiarism was detected
                - plagiarized_content (List): List of detected plagiarized content with sources
                - total_sentences (int): Total number of sentences checked
                - plagiarized_sentences (List): List of sentences detected as plagiarized
                - percent_plagiarized (float): Percentage of text detected as plagiarized
        :rtype: Dict
        :raises ValueError: If the API returns an error or if the response is invalid
        """
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
        }
        input_json = {
            "text": text,
            "source": SOURCE_VERSION,
        }

        response = requests.post(PLAGIARISM_API_ENDPOINT, json=input_json, headers=headers, timeout=90)
        if response.status_code != 200:
            raise ValueError(f"Error returned by API: [{response.status_code}] {response.text}")
        response_json = response.json()
        if "error" in response_json:
            raise ValueError(f"Error returned by API: {response_json['error']}")
        return response_json


    def predict_extended(self, text: str) -> Dict:
        """
        Classify text as AI- or human-written with extended analysis.

        Sends a request to the Pangram Text Extended API and returns precise, windowed results using adaptive boundaries 

        .. deprecated:: 0.1.11
           This method is deprecated. Use :meth:`predict` instead for better performance. This method will be removed by April 1st, 2026. 

        :param text: The text to be classified.
        :type text: str
        :return: The extended classification result from the API, as a dict with the following fields:

                - text (str): The input text.
                - avg_ai_likelihood (float): Weighted average AI likelihood score.
                - max_ai_likelihood (float): Maximum AI likelihood score among all windows.
                - prediction (str): Long-form prediction string.
                - prediction_short (str): Short-form prediction string.
                - headline (str): Classification headline.
                - windows (list): List of text windows and their classifications.
                - window_likelihoods (list): AI likelihood scores for each window.
                - window_indices (list): Indices for each window.
                - percent_human (float): Percentage classified as human-written.
                - percent_ai (float): Percentage classified as AI-written.
                - percent_mixed (float): Percentage classified as mixed.
                - metadata (dict): Additional metadata about the analysis.
                - version (str): Analysis version identifier.
        :rtype: Dict
        :raises ValueError: If the API returns an error or if the response is invalid
        """
        warnings.warn(
            "predict_extended() is deprecated. Use predict() instead to access Pangram's latest model. This method will be removed by April 1st, 2026.",
            DeprecationWarning,
            stacklevel=2
        )
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
        }
        input_json = {
            "text": text,
            "source": SOURCE_VERSION,
        }

        response = requests.post(TEXT_EXTENDED_API_ENDPOINT, json=input_json, headers=headers, timeout=90)
        if response.status_code != 200:
            raise ValueError(f"Error returned by API: [{response.status_code}] {response.text}")
        response_json = response.json()
        if "error" in response_json:
            raise ValueError(f"Error returned by API: {response_json['error']}")
        return response_json
