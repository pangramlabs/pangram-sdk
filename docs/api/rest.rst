Inference API
=============

The Inference API allows you to submit text and receive an AI likelihood score.


.. http:post:: https://text.api.pangram.com

  .. warning::
     Posting to the root route (/) for this endpoint is deprecated. Use the v3 endpoint to access the latest version of Pangram. This endpoint will be removed by April 1st, 2026.

  :<json string text: The input text to classify.
  :<json bool return_ai_sentences: (Optional, default is False) If True, then return a list of the most indicative AI sentences.
  :>json float ai_likelihood: The classification of the text, on a scale from 0.0 (human) to 1.0 (AI).
  :>json string text: The classified text.
  :>json string prediction: A string representing the classification.
  :>json list ai_sentences: If return_ai_sentences was True, then a list of the most indicative AI sentences.

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

    POST https://text.api.pangram.com HTTP/1.1
    Content-Type: application/json
    x-api-key: your_api_key_here

    {
      "text": "The text to analyze"
    }

  **Example Response**

  .. code-block:: json

    {
      "text": "The text to analyze",
      "prediction": "Likely AI",
      "ai_likelihood": 0.92
    }

.. http:post:: https://text.api.pangram.com/v3

  :<json string text: The input text to analyze with Pangram.
  :>json string text: The input text that was analyzed.
  :>json string version: The API version identifier.
  :>json string headline: Classification headline summarizing the result.
  :>json string prediction: Long-form prediction string representing the classification.
  :>json string prediction_short: Short-form prediction string.
  :>json float fraction_ai: Fraction of text classified as AI-written (0.0-1.0).
  :>json float fraction_ai_assisted: Fraction of text classified as AI-assisted (0.0-1.0).
  :>json float fraction_human: Fraction of text classified as human-written (0.0-1.0).
  :>json int num_ai_segments: Number of text segments classified as AI.
  :>json int num_ai_assisted_segments: Number of text segments classified as AI-assisted.
  :>json int num_human_segments: Number of text segments classified as human.
  :>json array windows: List of text segments (windows) analyzed individually. Each window contains the window text, label (descriptive classification like "AI-Generated", "Moderately AI-Assisted"), ai_assistance_score (float between 0 and 1), confidence (string like "High", "Medium", "Low"), start_index, end_index, word_count, and token_length.

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

    POST https://text.api.pangram.com/v3 HTTP/1.1
    Content-Type: application/json
    x-api-key: your_api_key_here

    {
      "text": "The text to analyze with V3 classification"
    }

  **Example Response**

  .. code-block:: json

    {
      "text": "The text to analyze with V3 classification",
      "version": "3.0",
      "headline": "AI Detected",
      "prediction": "We are confident that this document is a mix of AI-generated, AI-assisted, and human-written content",
      "prediction_short": "Mixed",
      "fraction_ai": 0.70,
      "fraction_ai_assisted": 0.20,
      "fraction_human": 0.10,
      "num_ai_segments": 7,
      "num_ai_assisted_segments": 2,
      "num_human_segments": 1,
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
          "text": "with V3 classification",
          "label": "Moderately AI-Assisted",
          "ai_assistance_score": 0.45,
          "confidence": "Medium",
          "start_index": 20,
          "end_index": 49,
          "word_count": 4,
          "token_length": 5
        }
      ]
    }

.. http:post:: https://text-batch.api.pangram.com

  .. warning::
     This endpoint is deprecated. Use the v3 endpoint instead for better performance. This endpoint will be removed by April 1st, 2026.

  :<json array text: An array of input texts to classify.
  :>json array responses: The classification results as a list, each item containing "text", "ai_likelihood", and "prediction". Each item in the array is the same as a response from a single text prediction.

  **Batch Inference**

    **Request Headers**

    .. code-block:: json

      {
        "Content-Type": "application/json",
        "x-api-key": "<api-key>"
      }

    **Request Body**

    .. code-block:: json

      {
        "text": ["<text1>", "<text2>", "..."]
      }

    **Example Request**

    .. code-block:: http

      POST https://text-batch.api.pangram.com HTTP/1.1
      Content-Type: application/json
      x-api-key: your_api_key_here

      {
        "text": ["The first text to analyze", "The second text to analyze"]
      }

    **Example Response**

    .. code-block:: json

      {
        "responses": [
          {
            "text": "The first text to analyze",
            "prediction": "Likely AI",
            "ai_likelihood": 0.92
          },
          {
            "text": "The second text to analyze",
            "prediction": "Possibly AI",
            "ai_likelihood": 0.58
          }
        ]
      }

.. http:post:: https://text-sliding.api.pangram.com

  .. warning::
     This endpoint is deprecated. Use the text-extended endpoint instead for better performance. This endpoint will be removed by April 1st, 2026.

  :<json string text: The input text to segment into windows and classify.
  :<json bool return_ai_sentences: (Optional, default is False) If True, then return a list of the most indicative AI sentences.
  :>json string text: The classified text.
  :>json float ai_likelihood: The classification of the text, on a scale from 0.0 (human) to 1.0 (AI).
  :>json float max_ai_likelihood: The maximum AI likelihood score among all windows.
  :>json float avg_ai_likelihood: The average AI likelihood score among all windows.
  :>json string prediction: A string representing the classification.
  :>json string short_prediction: A short string representing the classification ("AI", "Human", "Mixed").
  :>json float fraction_ai_content: The fraction of windows that are classified as AI.
  :>json array windows: A list of windows and their individual classifications. Each object in the array is the response from a single text prediction.
  :>json list ai_sentences: If return_ai_sentences was True, then a list of the most indicative AI sentences.

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

    POST https://text.api.pangram.com HTTP/1.1
    Content-Type: application/json
    x-api-key: your_api_key_here

    {
      "text": "Extremely long text."
    }

  **Example Response**

  .. code-block:: json

    {
      "text": "Extremely long text.",
      "prediction": "Highly likely AI",
      "ai_likelihood": 1.0,
      "max_ai_likelihood": 1.0,
      "avg_ai_likelihood": 0.6,
      "fraction_ai_content": 0.5,
      "windows": [
        {
          "text": "Extremely long",
          "ai_likelihood": 1.0,
          "prediction": "Highly likely AI"
        },
        {
          "text": "long text.",
          "ai_likelihood": 0.2,
          "prediction": "Unlikely AI"
        }
      ]
    }

.. http:post:: https://dashboard-text.api.pangram.com

  .. warning::
     This endpoint is deprecated. Use the text-extended endpoint with the dashboard flag instead. This endpoint will be removed by April 1st, 2026.

  :<json string text: The input text to classify.
  :>json float ai_likelihood: The classification of the text, on a scale from 0.0 (human) to 1.0 (AI).
  :>json string prediction: A string representing the classification.
  :>json string short_prediction: A short string representing the classification ("AI", "Human", "Mixed").
  :>json string dashboard_link: A link to the dashboard page containing the full classification result.
  :>json float fraction_ai_content: The fraction of windows that are classified as AI.
  :>json float max_ai_likelihood: The maximum AI likelihood score among all windows.
  :>json float avg_ai_likelihood: The average AI likelihood score among all windows.
  :>json array windows: A list of windows and their individual classifications. Each object in the array is the response from a single text prediction.

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

    POST https://text.api.pangram.com HTTP/1.1
    Content-Type: application/json
    x-api-key: your_api_key_here

    {
      "text": "Extremely long text."
    }

  **Example Response**

  .. code-block:: json

    {
      "text": "Extremely long text.",
      "prediction": "Highly likely AI",
      "ai_likelihood": 1.0,
      "dashboard_link": "https://www.pangram.com/history/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "max_ai_likelihood": 1.0,
      "avg_ai_likelihood": 0.6,
      "fraction_ai_content": 0.5,
      "windows": [
        {
          "text": "Extremely long",
          "ai_likelihood": 1.0,
          "prediction": "Highly likely AI"
        },
        {
          "text": "long text.",
          "ai_likelihood": 0.2,
          "prediction": "Unlikely AI"
        }
      ]
    }

.. http:post:: https://text-extended.api.pangram.com

  :<json string text: The input text to classify with extended analysis.
  :<json boolean dashboard: Optional flag to enable dashboard integration (default: false).
  :<json boolean is_public: Optional flag to control visibility in dashboard (default: true).
  :>json string text: The input text that was analyzed.
  :>json float avg_ai_likelihood: Weighted average AI likelihood score across all windows.
  :>json float max_ai_likelihood: Maximum AI likelihood score among all windows.
  :>json string prediction: Long-form prediction string representing the classification.
  :>json string prediction_short: Short-form prediction string ("AI", "Human", "Mixed").
  :>json string headline: Classification headline summarizing the result.
  :>json array windows: List of text segments (windows) analyzed individually. Each window contains text, ai_likelihood, label (str), confidence (str), start_index, end_index, and word_count.
  :>json array window_likelihoods: AI likelihood scores for each window (list of values from 0.0 to 1.0)
  :>json array window_indices: Indices indicating the position of each window in the original text (list of tuples (start_char_index, end_char_index))
  :>json float fraction_human: Fraction of text classified as human-written (0.0-1.0).
  :>json float fraction_ai: Fraction of text classified as AI-written (0.0-1.0).
  :>json float fraction_mixed: Fraction of text classified as mixed content (0.0-1.0).
  :>json object metadata: Additional metadata about the analysis.
  :>json string version: Analysis version identifier ("adaptive_boundaries").
  :>json string dashboard_link: Optional dashboard link (only present when dashboard=true). is_public controls visibility of dashboard link, to only your account or all users. 

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
      "dashboard": false,
      "is_public": true
    }

  **Example Request**

  .. code-block:: http

    POST https://text-extended.api.pangram.com HTTP/1.1
    Content-Type: application/json
    x-api-key: your_api_key_here

    {
      "text": "The text to analyze with extended classification",
      "dashboard": true,
      "is_public": true
    }

  **Example Response**

  .. code-block:: json

    {
      "text": "The text to analyze with extended classification",
      "avg_ai_likelihood": 0.75,
      "max_ai_likelihood": 0.92,
      "prediction": "Primarily AI-generated, or heavily AI-assisted",
      "prediction_short": "AI",
      "headline": "AI Detected",
      "windows": [
        {
          "text": "The text to analyze",
          "ai_likelihood": 0.85,
          "label": "AI",
          "confidence": "Medium",
          "start_index": 0,
          "end_index": 19,
          "word_count": 4
        },
        {
          "text": "with extended classification",
          "ai_likelihood": 0.65,
          "label": "AI",
          "confidence": "Low",
          "start_index": 20,
          "end_index": 47,
          "word_count": 3
        }
      ],
      "window_likelihoods": [0.85, 0.65],
      "window_indices": [[0, 19], [20, 47]],
      "fraction_human": 0.25,
      "fraction_ai": 0.70,
      "fraction_mixed": 0.05,
      "metadata": {
        "request_id": "123e4567-e89b-12d3-a456-426614174000"
      },
      "version": "adaptive_boundaries",
      "dashboard_link": "https://www.pangram.com/history/123e4567-e89b-12d3-a456-426614174000"
    }

Plagiarism Detection API
========================

The Plagiarism Detection API allows you to check text for potential plagiarism by comparing it against a vast database of online content.

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

- `400 Bad Request` - If the request body is not properly formatted.
- `401 Unauthorized` - If the `x-api-key` is missing, invalid, or does not have enough credits to process the request.
- `500 Internal Server Error` - If there is an error processing the request.

Please reach out at `support@pangram.com <mailto:support@pangram.com>`_ if you are running into errors with your requests.
