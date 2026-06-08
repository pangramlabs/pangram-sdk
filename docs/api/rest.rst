Inference API
=============

The Inference API accepts text, creates a task, and returns a task ID.
Poll the task endpoint until the stage is ``STAGE_SUCCESS`` or ``STAGE_FAILED``.

.. http:post:: https://text.external-api.pangram.com/task

  :<json string text: The input text to analyze with Pangram.
  :<json boolean public_dashboard_link: Whether to include a public dashboard link in the completed response. Defaults to false.
  :>json string task_id: The ID of the async inference task.

  **Request Headers**

  .. code-block:: json

    {
      "Content-Type": "application/json",
      "x-api-key": "<api-key>"
    }

  **Request Body**

  .. code-block:: json

    {
      "text": "<text>",
      "public_dashboard_link": false
    }

  **Example Request**

  .. code-block:: http

    POST https://text.external-api.pangram.com/task HTTP/1.1
    Content-Type: application/json
    x-api-key: your_api_key_here

    {
      "text": "The text to analyze",
      "public_dashboard_link": true
    }

  **Example Response**

  .. code-block:: json

    {
      "task_id": "123e4567-e89b-12d3-a456-426614174000"
    }

.. http:get:: https://text.external-api.pangram.com/task/(string:task_id)

  :>json string task_id: The ID of the async inference task. Present while the task is in progress.
  :>json string stage: Current task stage. Terminal stages are ``STAGE_SUCCESS`` and ``STAGE_FAILED``.
  :>json string text: The input text that was analyzed. Present on success.
  :>json string version: The API version identifier. Present on success.
  :>json string headline: Classification headline summarizing the result. Present on success.
  :>json string prediction: Long-form prediction string representing the classification. Present on success.
  :>json string prediction_short: Short-form prediction string. Present on success.
  :>json float fraction_ai: Fraction of text classified as AI-written (0.0-1.0). Present on success.
  :>json float fraction_ai_assisted: Fraction of text classified as AI-assisted (0.0-1.0). Present on success.
  :>json float fraction_human: Fraction of text classified as human-written (0.0-1.0). Present on success.
  :>json int num_ai_segments: Number of text segments classified as AI. Present on success.
  :>json int num_ai_assisted_segments: Number of text segments classified as AI-assisted. Present on success.
  :>json int num_human_segments: Number of text segments classified as human. Present on success.
  :>json array windows: List of analyzed text windows. Each window includes text, label, ai_assistance_score, confidence, start_index, end_index, word_count, and token_length. Present on success.
  :>json string dashboard_link: A link to the dashboard page containing the full classification result. Present on success when public_dashboard_link is true.

  **Request Headers**

  .. code-block:: json

    {
      "x-api-key": "<api-key>"
    }

  **In-Progress Response**

  .. code-block:: json

    {
      "task_id": "123e4567-e89b-12d3-a456-426614174000",
      "stage": "STAGE_PREPROCESSING"
    }

  **Success Response**

  .. code-block:: json

    {
      "stage": "STAGE_SUCCESS",
      "text": "The text to analyze",
      "version": "3.0",
      "headline": "AI Detected",
      "prediction": "We are confident that this document contains AI-generated or AI-assisted content.",
      "prediction_short": "Mixed",
      "fraction_ai": 0.70,
      "fraction_ai_assisted": 0.20,
      "fraction_human": 0.10,
      "num_ai_segments": 7,
      "num_ai_assisted_segments": 2,
      "num_human_segments": 1,
      "dashboard_link": "https://www.pangram.com/history/123e4567-e89b-12d3-a456-426614174000",
      "windows": [
        {
          "text": "The text to analyze",
          "label": "AI-Generated",
          "ai_assistance_score": 0.85,
          "confidence": "High",
          "start_index": 0,
          "end_index": 19,
          "word_count": 4,
          "token_length": 5
        },
        {
          "text": "with classification",
          "label": "Moderately AI-Assisted",
          "ai_assistance_score": 0.45,
          "confidence": "Medium",
          "start_index": 20,
          "end_index": 49,
          "word_count": 2,
          "token_length": 3
        }
      ]
    }

  **Failed Response**

  .. code-block:: json

    {
      "stage": "STAGE_FAILED",
      "text": "",
      "version": "",
      "headline": "preprocessing: Input text contains no valid text after preprocessing",
      "prediction": "",
      "prediction_short": "",
      "fraction_ai": 0.0,
      "fraction_ai_assisted": 0.0,
      "fraction_human": 0.0,
      "num_ai_segments": 0,
      "num_ai_assisted_segments": 0,
      "num_human_segments": 0,
      "windows": []
    }

Bulk API
========

The Bulk API accepts many texts, queues them as asynchronous AI detection work,
and returns a bulk job ID. Poll the bulk status endpoint until the status is
``succeeded``, ``failed``, or ``partial``.

Bulk metadata and results are retained for 48 hours after the job reaches a
terminal status. ``created_at`` and ``completed_at`` are returned as Unix epoch
seconds encoded as strings, such as ``"1760000000.0"``.

The launch bulk limit is 1,000 billable units per request. A billable unit is
one started 1,000-word block per valid item, with a minimum of one unit per
item. There is no separate item-count limit, but normal request-body limits
still apply.

.. http:post:: https://text.external-api.pangram.com/bulk

  :<json array text: A list of input texts. Provide either ``text`` or ``items``.
  :<json array items: A list of objects with ``text`` and optional ``id`` fields. Provide either ``items`` or ``text``.
  :>json string bulk_id: The ID of the bulk job.
  :>json string status: Initial status, usually ``queued`` or ``failed`` if every item failed immediate validation.
  :>json int total_items: Total number of submitted items.
  :>json array accepted_items: Items accepted for processing. Each item includes ``index``, optional ``id``, and ``task_id``.
  :>json array failed_items: Items that failed immediate validation. Each item includes ``index``, optional ``id``, ``stage``, and ``error``.

  **Request Headers**

  .. code-block:: json

    {
      "Content-Type": "application/json",
      "x-api-key": "<api-key>"
    }

  **Request Body**

  .. code-block:: json

    {
      "items": [
        {"id": "row-001", "text": "First text to analyze"},
        {"id": "row-002", "text": "Second text to analyze"}
      ]
    }

  **Example Response**

  .. code-block:: json

    {
      "bulk_id": "blk_123",
      "status": "queued",
      "total_items": 2,
      "accepted_items": [
        {"index": 0, "id": "row-001", "task_id": "123e4567-e89b-12d3-a456-426614174000"},
        {"index": 1, "id": "row-002", "task_id": "223e4567-e89b-12d3-a456-426614174000"}
      ],
      "failed_items": []
    }

.. http:get:: https://text.external-api.pangram.com/bulk/(string:bulk_id)

  :>json string bulk_id: The ID of the bulk job.
  :>json string status: One of ``queued``, ``running``, ``succeeded``, ``failed``, or ``partial``.
  :>json int total_items: Total number of submitted items.
  :>json int accepted: Number of items accepted for processing.
  :>json int succeeded: Number of items that completed successfully.
  :>json int failed: Number of items that failed.
  :>json string created_at: Job creation timestamp as Unix epoch seconds encoded as a string.
  :>json string completed_at: Job completion timestamp as Unix epoch seconds encoded as a string, or null while non-terminal.

  **Example Response**

  .. code-block:: json

    {
      "bulk_id": "blk_123",
      "status": "partial",
      "total_items": 3,
      "accepted": 2,
      "succeeded": 2,
      "failed": 1,
      "created_at": "1760000000.0",
      "completed_at": "1760000030.0"
    }

.. http:get:: https://text.external-api.pangram.com/bulk/(string:bulk_id)/items

  :query int offset: Zero-based item offset. Defaults to 0.
  :query int limit: Maximum number of items to return. Defaults to 100 and can be at most 1000.
  :>json string bulk_id: The ID of the bulk job.
  :>json int offset: The returned page offset.
  :>json int limit: The returned page limit.
  :>json int total_items: Total number of submitted items.
  :>json array items: Item metadata. Each item includes ``index``, optional ``id``, ``task_id``, ``stage``, and optional ``error``.

  **Example Response**

  .. code-block:: json

    {
      "bulk_id": "blk_123",
      "offset": 0,
      "limit": 100,
      "total_items": 2,
      "items": [
        {
          "index": 0,
          "id": "row-001",
          "task_id": "123e4567-e89b-12d3-a456-426614174000",
          "stage": "STAGE_SUCCESS",
          "error": null
        }
      ]
    }

.. http:get:: https://text.external-api.pangram.com/bulk/(string:bulk_id)/results

  :query int offset: Zero-based item offset. Defaults to 0.
  :query int limit: Maximum number of items to return. Defaults to 100 and can be at most 1000.
  :>json string bulk_id: The ID of the bulk job.
  :>json int offset: The returned page offset.
  :>json int limit: The returned page limit.
  :>json int total_items: Total number of submitted items.
  :>json array items: Result items. Successful completed items include ``result`` with the same shape returned by the task endpoint. In-progress items have ``result`` set to null.
  :>json array failed_items: Failed item metadata for the requested page.

  **Example Response**

  .. code-block:: json

    {
      "bulk_id": "blk_123",
      "offset": 0,
      "limit": 100,
      "total_items": 2,
      "items": [
        {
          "index": 0,
          "id": "row-001",
          "task_id": "123e4567-e89b-12d3-a456-426614174000",
          "stage": "STAGE_SUCCESS",
          "error": null,
          "result": {
            "text": "First text to analyze",
            "version": "3.3",
            "prediction": "We believe this is human-written",
            "prediction_short": "Human",
            "fraction_ai": 0.0,
            "fraction_ai_assisted": 0.0,
            "fraction_human": 1.0,
            "headline": "Human Written",
            "num_ai_segments": 0,
            "num_ai_assisted_segments": 0,
            "num_human_segments": 1,
            "windows": []
          }
        }
      ],
      "failed_items": []
    }

Plagiarism Detection API
========================

The Plagiarism Detection API checks text for potential plagiarism by comparing it against online content.

.. http:post:: https://plagiarism.api.pangram.com

  :<json string text: The input text to check for plagiarism.
  :>json string text: The input text that was checked.
  :>json bool plagiarism_detected: Whether plagiarism was detected in the text.
  :>json array plagiarized_content: A list of detected plagiarized content, including source URLs and matched text.
  :>json int total_sentences: Total number of sentences in the input text.
  :>json array plagiarized_sentences: List of sentences that were detected as plagiarized.
  :>json float percent_plagiarized: Percentage of the text that was detected as plagiarized.

  **Request Headers**

  .. code-block:: json

    {
      "Content-Type": "application/json",
      "x-api-key": "<api-key>"
    }

  **Request Body**

  .. code-block:: json

    {
      "text": "<text>"
    }

  **Example Request**

  .. code-block:: http

    POST https://plagiarism.api.pangram.com HTTP/1.1
    Content-Type: application/json
    x-api-key: your_api_key_here

    {
      "text": "The text to check for plagiarism"
    }

  **Example Response**

  .. code-block:: json

    {
      "text": "The text to check for plagiarism",
      "plagiarism_detected": true,
      "plagiarized_content": [
        {
          "source_url": "https://example.com/source",
          "matched_text": "The text to check for plagiarism",
          "similarity_score": 0.95
        }
      ],
      "total_sentences": 1,
      "plagiarized_sentences": 1,
      "percent_plagiarized": 100.0
    }

**Errors**

The API may return the following error codes:

- ``400 Bad Request`` - If the request body is not properly formatted.
- ``401 Unauthorized`` - If the ``x-api-key`` is missing or invalid.
- ``402 Payment Required`` - If the account has insufficient credits.
- ``403 Forbidden`` - If the API key does not own the requested task.
- ``404 Not Found`` - If the requested task does not exist.
- ``422 Unprocessable Entity`` - If the input text is invalid.
- ``429 Too Many Requests`` - If the API key exceeds its configured rate limit.
- ``500 Internal Server Error`` - If there is an error processing the request.

Please reach out at `support@pangram.com <mailto:support@pangram.com>`_ if you are running into errors with your requests.
