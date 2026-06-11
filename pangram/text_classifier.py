import requests
import os
import time
import warnings
from typing import List, Dict, Optional, Tuple, Union

SOURCE_VERSION = "python_sdk_0.3.0"

API_ENDPOINT = 'https://text.external-api.pangram.com'
FILE_UPLOAD_API_ENDPOINT = 'https://file-external.api.pangram.com'
PLAGIARISM_API_ENDPOINT = 'https://plagiarism.api.pangram.com'
ASYNC_SUCCESS_STAGE = 'STAGE_SUCCESS'
ASYNC_FAILED_STAGE = 'STAGE_FAILED'
BULK_TERMINAL_STATUSES = {'succeeded', 'failed', 'partial'}
DEFAULT_PREDICT_TIMEOUT_SECONDS = 300
DEFAULT_BULK_TIMEOUT_SECONDS = 3600
DEFAULT_POLL_INTERVAL_SECONDS = 0.5
MIN_POLL_INTERVAL_SECONDS = 0.1
HTTP_REQUEST_TIMEOUT_SECONDS = 10
MAX_BULK_PAGE_LIMIT = 1000

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

    def _auth_headers(self) -> Dict[str, str]:
        return {
            'x-api-key': self.api_key,
        }

    def _headers(self) -> Dict[str, str]:
        return {
            'Content-Type': 'application/json',
            **self._auth_headers(),
        }

    def _request_timeout(self, deadline: float) -> float:
        remaining = deadline - time.monotonic()
        return max(0.1, min(HTTP_REQUEST_TIMEOUT_SECONDS, remaining))

    def _parse_response_json(self, response: requests.Response, expected_status_codes: Tuple[int, ...] = (200,)):
        if response.status_code not in expected_status_codes:
            raise ValueError(f"Error returned by API: [{response.status_code}] {response.text}")
        try:
            response_json = response.json()
        except ValueError as exc:
            raise ValueError(f"Error returned by API: non-JSON response: {response.text}") from exc
        if isinstance(response_json, dict) and "error" in response_json:
            raise ValueError(f"Error returned by API: {response_json['error']}")
        return response_json

    def submit_bulk(
        self,
        text: Optional[List[str]] = None,
        items: Optional[List[Dict[str, str]]] = None,
    ) -> Dict:
        """
        Submit a Bulk API job for asynchronous AI detection.

        Provide either ``text`` as a list of input strings or ``items`` as a
        list of dictionaries with ``text`` and an optional customer-defined
        ``id``. The response includes a ``bulk_id`` for polling and immediate
        per-item validation failures, if any.

        :param text: A list of input texts to analyze.
        :type text: List[str], optional
        :param items: A list of item dictionaries. Each item must include
                      ``text`` and may include ``id``.
        :type items: List[Dict[str, str]], optional
        :return: Bulk submission response containing ``bulk_id``, ``status``,
                 ``total_items``, ``accepted_items``, and ``failed_items``.
        :rtype: Dict
        :raises ValueError: If both or neither payload shapes are provided, or
                            if the API returns an error.
        """
        if (text is None and items is None) or (text is not None and items is not None):
            raise ValueError("Provide exactly one of text or items")

        payload = {"items": items} if items is not None else {"text": text}
        try:
            response = requests.post(
                f"{API_ENDPOINT}/bulk",
                json=payload,
                headers=self._headers(),
                timeout=HTTP_REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise ValueError(f"Pangram API request failed while submitting bulk job: {exc}") from exc
        response_json = self._parse_response_json(response, expected_status_codes=(202,))
        if not isinstance(response_json, dict):
            raise ValueError(f"Error returned by API: invalid bulk response: {response_json}")
        return response_json

    def _fetch_bulk_status(self, bulk_id: str, request_timeout: float) -> Dict:
        response = requests.get(
            f"{API_ENDPOINT}/bulk/{bulk_id}",
            headers=self._headers(),
            timeout=request_timeout,
        )
        response_json = self._parse_response_json(response)
        if not isinstance(response_json, dict):
            raise ValueError(f"Error returned by API: invalid bulk status response: {response_json}")
        return response_json

    def get_bulk_status(self, bulk_id: str) -> Dict:
        """
        Fetch the current status for a Bulk API job.

        :param bulk_id: The bulk job ID returned by :meth:`submit_bulk`.
        :type bulk_id: str
        :return: Bulk status response containing counters and timestamps.
        :rtype: Dict
        :raises ValueError: If the API returns an error or an invalid response.
        """
        try:
            return self._fetch_bulk_status(bulk_id, HTTP_REQUEST_TIMEOUT_SECONDS)
        except requests.RequestException as exc:
            raise ValueError(f"Pangram API request failed while fetching bulk status: {exc}") from exc

    def get_bulk_items(self, bulk_id: str, offset: int = 0, limit: int = 100) -> Dict:
        """
        Fetch paginated item metadata for a Bulk API job.

        :param bulk_id: The bulk job ID returned by :meth:`submit_bulk`.
        :type bulk_id: str
        :param offset: Zero-based item offset. Defaults to 0.
        :type offset: int
        :param limit: Maximum number of items to return. The API allows up to 1000.
        :type limit: int
        :return: Paginated bulk item metadata.
        :rtype: Dict
        :raises ValueError: If the API returns an error or an invalid response.
        """
        try:
            response = requests.get(
                f"{API_ENDPOINT}/bulk/{bulk_id}/items",
                params={"offset": offset, "limit": limit},
                headers=self._headers(),
                timeout=HTTP_REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise ValueError(f"Pangram API request failed while fetching bulk items: {exc}") from exc
        response_json = self._parse_response_json(response)
        if not isinstance(response_json, dict):
            raise ValueError(f"Error returned by API: invalid bulk items response: {response_json}")
        return response_json

    def get_bulk_results_page(self, bulk_id: str, offset: int = 0, limit: int = 100) -> Dict:
        """
        Fetch one page of results for a Bulk API job.

        Completed successful items include a ``result`` field with the same
        response shape returned by :meth:`predict`. Items that are still running
        have ``result`` set to ``None``. Failed items are returned separately in
        ``failed_items``.

        :param bulk_id: The bulk job ID returned by :meth:`submit_bulk`.
        :type bulk_id: str
        :param offset: Zero-based item offset. Defaults to 0.
        :type offset: int
        :param limit: Maximum number of items to return. The API allows up to 1000.
        :type limit: int
        :return: Paginated bulk result response.
        :rtype: Dict
        :raises ValueError: If the API returns an error or an invalid response.
        """
        try:
            response = requests.get(
                f"{API_ENDPOINT}/bulk/{bulk_id}/results",
                params={"offset": offset, "limit": limit},
                headers=self._headers(),
                timeout=HTTP_REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise ValueError(f"Pangram API request failed while fetching bulk results: {exc}") from exc
        response_json = self._parse_response_json(response)
        if not isinstance(response_json, dict):
            raise ValueError(f"Error returned by API: invalid bulk results response: {response_json}")
        return response_json

    def get_bulk_results(self, bulk_id: str, page_size: int = MAX_BULK_PAGE_LIMIT) -> Dict:
        """
        Fetch all available results for a Bulk API job.

        This helper follows the paginated ``/bulk/{bulk_id}/results`` endpoint
        until every submitted item index has been covered. Failed items are
        returned separately in ``failed_items``. If the job is still running,
        unfinished accepted items are included in ``items`` with ``result`` set
        to ``None``.

        :param bulk_id: The bulk job ID returned by :meth:`submit_bulk`.
        :type bulk_id: str
        :param page_size: Number of submitted item slots to request per API call.
                          The API allows up to 1000.
        :type page_size: int
        :return: Aggregated bulk result response containing ``bulk_id``,
                 ``total_items``, ``items``, and ``failed_items``.
        :rtype: Dict
        :raises ValueError: If page_size is invalid, or if the API returns an
                            error or invalid response.
        """
        if page_size < 1 or page_size > MAX_BULK_PAGE_LIMIT:
            raise ValueError(f"page_size must be between 1 and {MAX_BULK_PAGE_LIMIT}")

        offset = 0
        total_items = None
        items = []
        failed_items = []
        response_bulk_id = bulk_id

        while total_items is None or offset < total_items:
            page = self.get_bulk_results_page(bulk_id, offset=offset, limit=page_size)
            response_bulk_id = page.get("bulk_id", response_bulk_id)
            page_total = page.get("total_items")
            if not isinstance(page_total, int):
                raise ValueError(f"Error returned by API: invalid bulk results total_items: {page}")
            total_items = page_total

            page_items = page.get("items")
            page_failed_items = page.get("failed_items")
            if not isinstance(page_items, list) or not isinstance(page_failed_items, list):
                raise ValueError(f"Error returned by API: invalid bulk results page: {page}")

            items.extend(page_items)
            failed_items.extend(page_failed_items)
            offset += page_size

        return {
            "bulk_id": response_bulk_id,
            "total_items": total_items or 0,
            "items": items,
            "failed_items": failed_items,
        }

    def wait_for_bulk(
        self,
        bulk_id: str,
        timeout: float = DEFAULT_BULK_TIMEOUT_SECONDS,
        poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
    ) -> Dict:
        """
        Poll a Bulk API job until it reaches a terminal status.

        Terminal statuses are ``succeeded``, ``failed``, and ``partial``.
        Completion time depends on the number and length of submitted items and
        current system load.

        :param bulk_id: The bulk job ID returned by :meth:`submit_bulk`.
        :type bulk_id: str
        :param timeout: Maximum seconds to wait for terminal completion.
        :type timeout: float
        :param poll_interval: Seconds to wait between polling attempts. Values
                              below 0.1 are clamped to 0.1.
        :type poll_interval: float
        :return: Terminal bulk status response.
        :rtype: Dict
        :raises ValueError: If timeout or poll interval values are invalid, or
                            if the API returns an error.
        :raises TimeoutError: If the bulk job does not complete before timeout.
        """
        if timeout <= 0:
            raise ValueError("timeout must be greater than 0")
        if poll_interval < 0:
            raise ValueError("poll_interval cannot be negative")

        deadline = time.monotonic() + timeout
        effective_poll_interval = max(MIN_POLL_INTERVAL_SECONDS, poll_interval)
        last_status = None

        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Pangram bulk job {bulk_id} did not complete within {timeout:.0f}s; last status={last_status}"
                )

            try:
                status_response = self._fetch_bulk_status(
                    bulk_id,
                    self._request_timeout(deadline),
                )
            except requests.RequestException as exc:
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"Pangram bulk job {bulk_id} did not complete within {timeout:.0f}s; last status={last_status}"
                    ) from exc
                sleep_for = min(effective_poll_interval, max(0.0, deadline - time.monotonic()))
                if sleep_for > 0:
                    time.sleep(sleep_for)
                continue

            last_status = status_response.get("status")
            if last_status in BULK_TERMINAL_STATUSES:
                return status_response

            sleep_for = min(effective_poll_interval, max(0.0, deadline - time.monotonic()))
            if sleep_for > 0:
                time.sleep(sleep_for)

    def _submit_prediction_task(self, text: str, deadline: float, public_dashboard_link: bool) -> str:
        try:
            response = requests.post(
                f"{API_ENDPOINT}/task",
                json={"text": text, "public_dashboard_link": public_dashboard_link},
                headers=self._headers(),
                timeout=self._request_timeout(deadline),
            )
        except requests.RequestException as exc:
            raise ValueError(f"Pangram API request failed while submitting prediction task: {exc}") from exc
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

            try:
                response = requests.get(
                    f"{API_ENDPOINT}/task/{task_id}",
                    headers=self._headers(),
                    timeout=self._request_timeout(deadline),
                )
            except requests.RequestException as exc:
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"Pangram prediction task {task_id} did not complete within {timeout:.0f}s"
                    ) from exc
                sleep_for = min(poll_interval, max(0.0, deadline - time.monotonic()))
                if sleep_for > 0:
                    time.sleep(sleep_for)
                continue
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
        :param poll_interval: Seconds to wait between polling attempts. Values below 0.1 are clamped to 0.1. Defaults to 0.5.
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
        return self._poll_prediction_task(
            task_id,
            deadline,
            timeout,
            max(MIN_POLL_INTERVAL_SECONDS, poll_interval),
        )

    def predict_files(
        self,
        file_paths: List[Union[str, os.PathLike]],
        public_dashboard_link: bool = False,
        timeout: float = DEFAULT_PREDICT_TIMEOUT_SECONDS,
    ) -> List[Dict]:
        """
        Upload one or more files for AI detection.

        Files are submitted to Pangram's file upload endpoint as multipart form
        data with one ``files`` field per uploaded .docx, .pdf, or .rtf file.
        Each returned result includes the extracted text, prediction fields,
        window-level analysis, and the uploaded ``filename``. When
        ``public_dashboard_link`` is true, each result also includes a
        ``dashboard_link`` URL.

        :param file_paths: Paths to files to upload and analyze.
        :type file_paths: List[Union[str, os.PathLike]]
        :param public_dashboard_link: Whether to create public dashboard links for the uploaded files. Defaults to False.
        :type public_dashboard_link: bool
        :param timeout: Maximum seconds to wait for the upload request to complete. Defaults to 300.
        :type timeout: float
        :return: A list of per-file result dictionaries returned by the API.
        :rtype: List[Dict]
        :raises ValueError: If no files are provided, if timeout is invalid, if
                            the API returns an error, or if the response is invalid.
        :raises requests.RequestException: File open errors are raised by Python before the request is sent.
        """
        if not file_paths:
            raise ValueError("file_paths must contain at least one file")
        if timeout <= 0:
            raise ValueError("timeout must be greater than 0")

        opened_files = []
        files_payload = []
        try:
            for file_path in file_paths:
                path = os.fspath(file_path)
                file_obj = open(path, "rb")
                opened_files.append(file_obj)
                files_payload.append(("files", (os.path.basename(path), file_obj)))

            try:
                response = requests.post(
                    FILE_UPLOAD_API_ENDPOINT,
                    files=files_payload,
                    data={"public_dashboard_link": str(public_dashboard_link).lower()},
                    headers=self._auth_headers(),
                    timeout=timeout,
                )
            except requests.RequestException as exc:
                raise ValueError(f"Pangram API request failed while uploading files: {exc}") from exc

            response_json = self._parse_response_json(response)
            if not isinstance(response_json, list):
                raise ValueError(f"Error returned by API: invalid file upload response: {response_json}")
            return response_json
        finally:
            for file_obj in opened_files:
                file_obj.close()

    def predict_file(
        self,
        file_path: Union[str, os.PathLike],
        public_dashboard_link: bool = False,
        timeout: float = DEFAULT_PREDICT_TIMEOUT_SECONDS,
    ) -> Dict:
        """
        Upload a single file for AI detection.

        This convenience method calls :meth:`predict_files` with one path and
        returns the first per-file result.

        :param file_path: Path to the file to upload and analyze.
        :type file_path: Union[str, os.PathLike]
        :param public_dashboard_link: Whether to create a public dashboard link for the uploaded file. Defaults to False.
        :type public_dashboard_link: bool
        :param timeout: Maximum seconds to wait for the upload request to complete. Defaults to 300.
        :type timeout: float
        :return: The per-file result dictionary returned by the API.
        :rtype: Dict
        :raises ValueError: If the API returns an error or an invalid response.
        """
        response_json = self.predict_files(
            [file_path],
            public_dashboard_link=public_dashboard_link,
            timeout=timeout,
        )
        if not response_json:
            raise ValueError("Error returned by API: empty file upload response")
        return response_json[0]


    def predict_short(self, text: str) -> Dict:
        """
        Classify text using the main async prediction endpoint.

        .. deprecated::
           This compatibility alias forwards to :meth:`predict`. Use
           :meth:`predict` directly for Pangram's current response schema.
           This method may be removed on August 1, 2026.

        :param text: The text to be classified.
        :type text: str
        :return: The same classification result returned by :meth:`predict`.
        :rtype: Dict
        """
        warnings.warn(
            "predict_short() is deprecated and forwards to predict(). "
            "Use predict() instead. This method may be removed on August 1, 2026.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.predict(text)


    def batch_predict(self, text_batch: List[str]) -> List[Dict]:
        """
        Classify a batch of text as AI-, AI-assisted, or human-written.

        This method iterates through the batch and calls predict() for each text.

        .. deprecated::
           This compatibility method forwards to :meth:`predict` once per
           input text. Use :meth:`submit_bulk` for asynchronous bulk jobs or
           :meth:`predict` for one-off calls. This method may be removed on
           August 1, 2026.

        :param text_batch: A list of strings to be classified.
        :type text_batch: List[str]
        :return: A list of classification results from the API for each text in the batch.
                 Each result is a dict with the same fields as returned by predict().
        :rtype: List[Dict]
        """
        warnings.warn(
            "batch_predict() is deprecated and forwards to predict() once per input text. "
            "Use submit_bulk() for asynchronous bulk jobs or predict() for one-off calls. "
            "This method may be removed on August 1, 2026.",
            DeprecationWarning,
            stacklevel=2,
        )
        results = []
        for text in text_batch:
            result = self.predict(text)
            results.append(result)
        return results


    def predict_with_dashboard_link(
        self,
        text: str,
        timeout: float = DEFAULT_PREDICT_TIMEOUT_SECONDS,
        poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
    ) -> Dict:
        """
        Classify text as AI-, AI-assisted, or human-written.

        Submits the text to Pangram's async inference endpoint, waits for completion,
        and returns analysis with a public dashboard link.

        :param text: The text to be classified.
        :type text: str
        :param timeout: Maximum seconds to wait for the async task to complete. Defaults to 300.
        :type timeout: float
        :param poll_interval: Seconds to wait between polling attempts. Values below 0.1 are clamped to 0.1. Defaults to 0.5.
        :type poll_interval: float
        :return: The classification result from the API, as a dict with the following fields:

                - text (string): The classified text.
                - dashboard_link (string): A link to a dashboard page containing the classification result.
                - stage (string): The terminal async task stage, normally "STAGE_SUCCESS".
                - prediction (string): Long-form prediction string describing the classification.
                - prediction_short (string): Short-form prediction string.
                - fraction_ai (float): Fraction of text classified as AI-written (0.0-1.0).
                - fraction_ai_assisted (float): Fraction of text classified as AI-assisted (0.0-1.0).
                - fraction_human (float): Fraction of text classified as human-written (0.0-1.0).
                - windows (list): List of text windows and their classifications.
        :rtype: dict
        :raises ValueError: If the API returns an error or if the response is invalid
        :raises TimeoutError: If the async task does not complete before timeout
        """
        return self.predict(
            text,
            public_dashboard_link=True,
            timeout=timeout,
            poll_interval=poll_interval,
        )

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
