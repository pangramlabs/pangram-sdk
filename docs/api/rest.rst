Inference API
=============

The Inference API allows you to submit text and receive a likelihood score. Use the batch inference API if classifying several documents, as it is more efficient and allows for higher throughput.

.. http:post:: https://text.api.pangramlabs.com

  :<json string text: The input text to classify.
  :>json float ai_likelihood: The classification of the text, on a scale from 0.0 (human) to 1.0 (AI).
  :>json string text: The classified text.
  :>json string prediction: A string representing the classification.

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

    POST https://text.api.pangramlabs.com HTTP/1.1
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

.. http:post:: https://text-batch.api.pangramlabs.com

  :<json array texts: The input texts to classify.
  :>json array responses: The classification results as a list, each item containing "text", "ai_likelihood", and "prediction".

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

      POST https://text-batch.api.pangramlabs.com HTTP/1.1
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

**Errors**

The following error responses are possible:

- `400 Bad Request` - If the request body is not properly formatted.
- `401 Unauthorized` - If the `x-api-key` is missing or invalid.
- `500 Internal Server Error` - If there is an error processing the request.
