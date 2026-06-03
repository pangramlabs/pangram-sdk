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
      "public_dashboard_link": false
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
- ``429 Too Many Requests`` - If the API key exceeds its configured rate limit.
- ``500 Internal Server Error`` - If there is an error processing the request.

Please reach out at `support@pangram.com <mailto:support@pangram.com>`_ if you are running into errors with your requests.
