Inference API
=============

The Inference API allows you to submit text and receive a likelihood score.

.. http:post:: https://api.checkfor.ai/inference

  :<json string input: The text for which the inference should be made.
  :>json float likelihood: The likelihood score of the inference.

  **Request Headers**

  .. code-block:: json

    {
      "Content-Type": "application/json",
      "x-api-key": "<api-key>"
    }

  **Request Body**

  .. code-block:: json

    {
      "input": "<text>"
    }

  **Example Request**

  .. code-block:: http

    POST /inference HTTP/1.1
    Host: api.checkfor.ai
    Content-Type: application/json
    x-api-key: your_api_key_here

    {
      "input": "The text to analyze"
    }

  **Example Response**

  .. code-block:: json

    {
      "likelihood": 0.92
    }

**Errors**

The following error responses are possible:

- `400 Bad Request` - If the request body is not properly formatted.
- `401 Unauthorized` - If the `x-api-key` is missing or invalid.
- `500 Internal Server Error` - If there is an error processing the request.
