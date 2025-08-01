Inference API
=============

The Inference API allows you to submit text and receive an AI likelihood score.

.. tip::
  Use the batch endpoint to maximize throughput when classifying multiple documents.

.. note::
  ``text.api.pangram.com`` and ``text-batch.api.pangram.com`` only use
  the first ~400 words of the input text when making its prediction.

  For accurate predictions on longer text with mixed human and AI content,
  break your document into chunks of ~400 words or use the sliding window API.

.. http:post:: https://text.api.pangram.com

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

.. http:post:: https://text-batch.api.pangram.com

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
