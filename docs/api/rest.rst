Inference API
=============

The Inference API accepts text, creates an async task, and returns a task ID.
Poll the task endpoint until the stage is ``STAGE_SUCCESS`` or ``STAGE_FAILED``.

.. http:post:: https://text-async.aws.pangram.com/task

  :<json string text: The input text to analyze with Pangram.
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
      "text": "<text>"
    }

  **Example Request**

  .. code-block:: http

    POST https://text-async.aws.pangram.com/task HTTP/1.1
    Content-Type: application/json
    x-api-key: your_api_key_here

    {
      "text": "The text to analyze"
    }

  **Example Response**

  .. code-block:: json

    {
      "task_id": "123e4567-e89b-12d3-a456-426614174000"
    }

.. http:get:: https://text-async.aws.pangram.com/task/(string:task_id)

  :>json string task_id: The ID of the async inference task.
  :>json string stage: Current task stage. Terminal stages are ``STAGE_SUCCESS`` and ``STAGE_FAILED``.
  :>json string text: The input text that was analyzed. Present on success.
  :>json string version: The API version identifier. Present on success.
  :>json string headline: Classification headline summarizing the result. Present on success.
  :>json string prediction: Long-form prediction string representing the classification. Present on success.
  :>json string prediction_short: Short-form prediction string. Present on success.
  :>json float fraction_ai: Fraction of text classified as AI-written (0.0-1.0). Present on success.
  :>json float fraction_ai_assisted: Fraction of text classified as AI-assisted (0.0-1.0). Present on success.
  :>json float fraction_human: Fraction of text classified as human-written (0.0-1.0). Present on success.
  :>json float fraction_mixed: Fraction of text classified as mixed. Present on success.
  :>json float avg_ai_likelihood: Average AI likelihood across analyzed windows. Present on success.
  :>json object fraction_breakdown: Confidence-level fraction breakdown. Present on success.
  :>json int num_ai_segments: Number of text segments classified as AI. Present on success.
  :>json int num_ai_assisted_segments: Number of text segments classified as AI-assisted. Present on success.
  :>json int num_human_segments: Number of text segments classified as human. Present on success.
  :>json array window_indices: Start/end character indices for each analyzed window. Present on success.
  :>json array windows: List of analyzed text windows. Each window includes text, ai_likelihood, label, confidence, start_index, end_index, word_count, token_length, and editlens metadata.

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
      "task_id": "123e4567-e89b-12d3-a456-426614174000",
      "stage": "STAGE_SUCCESS",
      "text": "The text to analyze",
      "version": "3.0",
      "headline": "AI Detected",
      "prediction": "We are confident that this document contains AI-generated or AI-assisted content.",
      "prediction_short": "Mixed",
      "fraction_ai": 0.70,
      "fraction_ai_assisted": 0.20,
      "fraction_human": 0.10,
      "fraction_mixed": 0.00,
      "avg_ai_likelihood": 0.78,
      "fraction_breakdown": {
        "ai": {
          "high-confidence": 0.50,
          "medium-confidence": 0.20,
          "low-confidence": 0.00
        },
        "ai-assisted": {
          "lightly": 0.10,
          "moderately": 0.10
        },
        "human": {
          "high-confidence": 0.10,
          "medium-confidence": 0.00,
          "low-confidence": 0.00
        }
      },
      "num_ai_segments": 7,
      "num_ai_assisted_segments": 2,
      "num_human_segments": 1,
      "window_indices": [[0, 19], [20, 49]],
      "windows": [
        {
          "text": "The text to analyze",
          "ai_likelihood": 0.85,
          "label": "AI-Generated",
          "confidence": "High",
          "start_index": 0,
          "end_index": 19,
          "word_count": 4,
          "token_length": 5,
          "editlens": {
            "prediction_text": "AI-Generated"
          }
        },
        {
          "text": "with classification",
          "ai_likelihood": 0.45,
          "label": "Moderately AI-Assisted",
          "confidence": "Medium",
          "start_index": 20,
          "end_index": 49,
          "word_count": 2,
          "token_length": 3,
          "editlens": {
            "prediction_text": "Moderately AI-Assisted"
          }
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
