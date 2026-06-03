import requests
import os
import time
import warnings
from typing import List, Dict, Optional

SOURCE_VERSION = "python_sdk_0.1.11"

API_ENDPOINT = 'https://text.external-api.pangram.com'
BATCH_API_ENDPOINT = 'https://text-batch.api.pangramlabs.com'
SLIDING_WINDOW_API_ENDPOINT = 'https://text-sliding.api.pangramlabs.com'
PLAGIARISM_API_ENDPOINT = 'https://plagiarism.api.pangram.com'
TEXT_EXTENDED_API_ENDPOINT = 'https://text-extended.api.pangramlabs.com'
ASYNC_SUCCESS_STAGE = 'STAGE_SUCCESS'
ASYNC_FAILED_STAGE = 'STAGE_FAILED'
DEFAULT_PREDICT_TIMEOUT_SECONDS = 300
DEFAULT_POLL_INTERVAL_SECONDS = 0.5
REQUEST_TIMEOUT_SECONDS = 10

class PangramText:
    def __init__(self, api_key: Optional[str] = None) -> None:
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

    def _headers(self) -> Dict[str, str]:
        return {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
        }

    def _request_timeout(self, deadline: float) -> float:
        remaining = deadline - time.monotonic()
        return max(0.1, min(REQUEST_TIMEOUT_SECONDS, remaining))

    def _parse_response_json(self, response: requests.Response):
        if response.status_code != 200:
            raise ValueError(f"Error returned by API: [{response.status_code}] {response.text}")
        try:
            response_json = response.json()
        except ValueError as exc:
            raise ValueError(f"Error returned by API: non-JSON response: {response.text}") from exc
        if isinstance(response_json, dict) and "error" in response_json:
            raise ValueError(f"Error returned by API: {response_json['error']}")
        return response_json

    def _submit_prediction_task(self, text: str, deadline: float, public_dashboard_link: bool) -> str:
        response = requests.post(
            f"{API_ENDPOINT}/task",
            json={"text": text, "public_dashboard_link": public_dashboard_link},
            headers=self._headers(),
            timeout=self._request_timeout(deadline),
        )
        response_json = self._parse_response_json(response)
        if not isinstance(response_json, dict):
            raise ValueError(f"Error returned by API: invalid task response: {response_json}")

        task_id = response_json.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError(f"Error returned by API: missing task_id in response: {response_json}")
        return task_id

    def _poll_prediction_task(
        self,
        task_id: str,
        deadline: float,
        timeout: float,
        poll_interval: float,
    ) -> Dict:
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Pangram prediction task {task_id} did not complete within {timeout:.0f}s")

            response = requests.get(
                f"{API_ENDPOINT}/task/{task_id}",
                headers=self._headers(),
                timeout=self._request_timeout(deadline),
            )
            response_json = self._parse_response_json(response)
            if not isinstance(response_json, dict):
                raise ValueError(f"Error returned by API: invalid task result: {response_json}")

            stage = response_json.get("stage")
            if stage == ASYNC_SUCCESS_STAGE:
                return response_json
            if stage == ASYNC_FAILED_STAGE:
                message = response_json.get("headline") or response_json.get("detail") or "task failed"
                raise ValueError(f"Error returned by API: task {task_id} failed: {message}")
            if stage is None:
                raise ValueError(f"Error returned by API: missing stage for task {task_id}")

            sleep_for = min(poll_interval, max(0.0, deadline - time.monotonic()))
            if sleep_for > 0:
                time.sleep(sleep_for)

    def predict(
        self,
        text: str,
        public_dashboard_link: bool = False,
        timeout: float = DEFAULT_PREDICT_TIMEOUT_SECONDS,
        poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
    ) -> Dict:
        """
        Classify text as AI-, AI-assisted, or human-written.

        Submits the text to Pangram's async inference endpoint, waits for completion,
        and returns analysis with windowed results.

        :param text: The text to be classified.
        :type text: str
        :param public_dashboard_link: Whether to include a public dashboard link in the completed response. Defaults to False.
        :type public_dashboard_link: bool
        :param timeout: Maximum seconds to wait for the async task to complete. Defaults to 300.
        :type timeout: float
        :param poll_interval: Seconds to wait between polling attempts. Defaults to 0.5.
        :type poll_interval: float
        :return: Pangram analysis with AI-assistance detection as a dict with the following fields:

                - stage (str): The terminal async task stage, normally "STAGE_SUCCESS".
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
                - dashboard_link (str): A link to the dashboard page containing the full classification result, if requested.
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
        :raises TimeoutError: If the async task does not complete before timeout
        """
        if timeout <= 0:
            raise ValueError("timeout must be greater than 0")
        if poll_interval < 0:
            raise ValueError("poll_interval cannot be negative")

        deadline = time.monotonic() + timeout
        task_id = self._submit_prediction_task(text, deadline, public_dashboard_link)
        return self._poll_prediction_task(task_id, deadline, timeout, poll_interval)


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
           This method is deprecated. Use :meth:`predict` instead.

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
            "predict_sliding_window() is deprecated. Use predict() instead.",
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
        Classify text as AI-, AI-assisted, or human-written.

        Sends a request to the Pangram Text API and returns the classification result.
        The async inference endpoint returns a dashboard link only when supported by the service.

        :param text: The text to be classified.
        :type text: str
        :return: The classification result from the API, as a dict with the following fields:

                - text (string): The classified text.
                - dashboard_link (string): A link to a dashboard page containing the classification result, if returned by the service.
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
           This method is deprecated. Use :meth:`predict` instead.

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
            "predict_extended() is deprecated. Use predict() instead.",
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
