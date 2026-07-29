Models API
==========

Use the Models API to discover the model selectors that an API key can
currently use. The response is entitlement- and availability-aware; do not
hard-code the returned catalog or assume that every API key sees the same
models. Clients should preserve the order returned by the server.

The Python SDK projects the response to a ``list[str]``:

.. code:: python

  available_models = pangram_client.list_models()
  # e.g., ["default", "pangram-4"]

.. http:get:: https://text.external-api.pangram.com/models

  :>json array models: Ordered public model selectors currently available to the authenticated API key.

  **Request Headers**

  .. code-block:: json

    {
      "x-api-key": "<api-key>"
    }

  **Example Response**

  .. code-block:: json

    {
      "models": [
        "default",
        "pangram-4"
      ]
    }

  An API key that is not enabled for Pangram 4 may receive only
  ``{"models": ["default"]}``. A missing or invalid API key returns
  ``401 Unauthorized``; an account with insufficient credits returns
  ``402 Payment Required``.

Inference API
=============

The Inference API accepts text, creates a task, and returns a task ID.
Poll the task endpoint until the stage is ``STAGE_SUCCESS`` or ``STAGE_FAILED``.
For backward compatibility, the REST endpoint currently accepts an omitted
``model`` and uses Pangram's server default. New integrations should always
send one of the values returned by the Models API.

The Python SDK exposes ``model`` as a keyword-only argument. For backward
compatibility, omitting it currently selects ``"default"`` and emits a
``DeprecationWarning``. Explicitly pass ``model="default"`` or
``model="pangram-4"`` in new code. After September 30, 2026, the SDK will
require callers to select a model explicitly:

.. code:: python

  result = pangram_client.predict(text, model="pangram-4")

.. http:post:: https://text.external-api.pangram.com/task

  :<json string text: The input text to analyze with Pangram.
  :<json string model: Optional model selector returned by the Models API. Defaults to ``"default"``.
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
      "model": "pangram-4",
      "public_dashboard_link": false
    }

  **Example Request**

  .. code-block:: http

    POST https://text.external-api.pangram.com/task HTTP/1.1
    Content-Type: application/json
    x-api-key: your_api_key_here

    {
      "text": "AI-assisted passage.\nHuman passage.",
      "model": "pangram-4",
      "public_dashboard_link": true
    }

  **Example Response**

  .. code-block:: json

    {
      "task_id": "123e4567-e89b-12d3-a456-426614174000"
    }

  **Model Selection Errors**

  - ``422 Unprocessable Entity`` - The selector is malformed or unknown.
  - ``403 Forbidden`` - The requested model is not enabled for the API key.
  - ``503 Service Unavailable`` - The requested model is temporarily unavailable.

.. http:get:: https://text.external-api.pangram.com/task/(string:task_id)

  :>json string task_id: The ID of the async inference task. Present while the task is in progress.
  :>json string stage: Current task stage. Terminal stages are ``STAGE_SUCCESS`` and ``STAGE_FAILED``.
  :>json string text: The analyzed text returned by the model. Pangram 4 may normalize it before inference. Present on success.
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
  :>json array windows: List of analyzed text windows. Each window includes ``text``, ``label``, ``ai_assistance_score``, string ``confidence``, ``start_index``, ``end_index``, ``word_count``, and ``token_length``. Pangram 4 windows also include ``is_humanized`` and ``humanizer_score``. Present on success.
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

  This example shows a Pangram 4 result. Pangram 4 returns ``version`` 4.0,
  uses ``"AI-Assisted"`` rather than lightly/moderately assisted window labels,
  and keeps ``confidence`` as one of the strings ``"Low"``, ``"Medium"``, or
  ``"High"``.

  .. code-block:: json

    {
      "stage": "STAGE_SUCCESS",
      "text": "AI-assisted passage. Human passage.",
      "version": "4.0",
      "headline": "AI Assisted",
      "prediction": "We believe that this text is a mix of AI-assisted and human-written content.",
      "prediction_short": "Mixed",
      "fraction_ai": 0.0,
      "fraction_ai_assisted": 0.6,
      "fraction_human": 0.4,
      "num_ai_segments": 0,
      "num_ai_assisted_segments": 1,
      "num_human_segments": 1,
      "dashboard_link": "https://www.pangram.com/history/123e4567-e89b-12d3-a456-426614174000",
      "windows": [
        {
          "text": "AI-assisted passage. ",
          "label": "AI-Assisted",
          "ai_assistance_score": 0.55,
          "confidence": "High",
          "start_index": 0,
          "end_index": 21,
          "word_count": 2,
          "token_length": 5,
          "is_humanized": true,
          "humanizer_score": 0.91
        },
        {
          "text": "Human passage.",
          "label": "Human Written",
          "ai_assistance_score": 0.02,
          "confidence": "Medium",
          "start_index": 21,
          "end_index": 35,
          "word_count": 2,
          "token_length": 4,
          "is_humanized": false,
          "humanizer_score": 0.0
        }
      ]
    }

  Every Pangram 4 window includes ``is_humanized`` and
  ``humanizer_score`` (0.0-1.0). Human windows and windows without humanizer
  evidence return ``false`` and ``0.0``. Models that do not expose the
  humanizer head omit both fields. Some accounts may also receive a 15-value
  ``edit_bucket_probabilities`` vector; that field is enabled separately from
  Pangram 4.

  Pangram 4 may normalize text before inference. It removes adversarial
  Unicode, replaces runs of line breaks and their surrounding horizontal
  whitespace with one space, and strips leading/trailing whitespace. Internal
  spacing, case, punctuation, and emoji are otherwise preserved. The returned
  top-level ``text`` is canonical. Window ``start_index`` and ``end_index`` are
  zero-based, end-exclusive character offsets into that returned text, so use
  ``text[start_index:end_index]`` rather than indexing into the original
  submitted string.

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

Completion time depends on the number and length of submitted items and current
system load. Use the bulk status endpoint to monitor progress.

Bulk metadata and results are retained for 48 hours after the job reaches a
terminal status. ``created_at`` and ``completed_at`` are returned as Unix epoch
seconds encoded as strings, such as ``"1760000000.0"``.

The launch bulk limit is 1,000 billable units per request. Billing follows the
model that actually serves the job: the standard model uses one unit per
started 1,000-word block, while Pangram 4 uses one unit per started 100-word
block. Each valid item has a minimum of one unit. There is no separate
item-count limit, but normal request-body limits still apply.

One ``model`` applies to the entire bulk job; per-item model selectors are not
supported. The REST endpoint accepts an omitted selector only for backward
compatibility and resolves it to ``"default"``. New integrations should send it
explicitly. The Python SDK's keyword-only ``model`` argument is temporarily
optional: omission selects ``"default"`` and emits a ``DeprecationWarning``.
After September 30, 2026, it will be required:

.. code:: python

  bulk = pangram_client.submit_bulk(
      items=[{"id": "row-001", "text": "Text to analyze"}],
      model="pangram-4",
  )

Invalid, unauthorized, or unavailable bulk model selectors return the same
``422``, ``403``, and ``503`` responses described for text inference.

.. http:post:: https://text.external-api.pangram.com/bulk

  :<json array text: A list of input texts. Provide either ``text`` or ``items``.
  :<json array items: A list of objects with ``text`` and optional ``id`` fields. Provide either ``items`` or ``text``.
  :<json string model: Optional model selector returned by the Models API. Applies to every item in the job and defaults to ``"default"``.
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
      ],
      "model": "pangram-4"
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
            "stage": "STAGE_SUCCESS",
            "text": "First text to analyze",
            "version": "4.0",
            "prediction": "We believe that this entire text is human-written.",
            "prediction_short": "Human",
            "fraction_ai": 0.0,
            "fraction_ai_assisted": 0.0,
            "fraction_human": 1.0,
            "headline": "Human Written",
            "num_ai_segments": 0,
            "num_ai_assisted_segments": 0,
            "num_human_segments": 1,
            "windows": [
              {
                "text": "First text to analyze",
                "label": "Human Written",
                "ai_assistance_score": 0.02,
                "confidence": "High",
                "start_index": 0,
                "end_index": 21,
                "word_count": 4,
                "token_length": 5,
                "is_humanized": false,
                "humanizer_score": 0.0
              }
            ]
          }
        }
      ],
      "failed_items": []
    }

File Upload API
===============

The File Upload API accepts one or more files as ``multipart/form-data`` and
returns one result object per uploaded file. Use this endpoint when you want
Pangram to extract text from ``.docx``, ``.pdf``, or ``.rtf`` documents and
create AI detection results. Each result uses the same prediction schema as the
text API, with the extracted ``text`` and uploaded ``filename`` included. When
``public_dashboard_link`` is ``true``, each result also includes a
``dashboard_link``.

File prediction currently uses Pangram's default model only. This endpoint, and
the Python SDK's ``predict_file()`` and ``predict_files()`` methods, do not
accept a ``model`` selector.

.. http:post:: https://file-external.api.pangram.com/

  **Request Headers**

  Do not set ``Content-Type`` manually for multipart requests. HTTP clients add
  the multipart boundary automatically.

  .. code-block:: json

    {
      "x-api-key": "<api-key>"
    }

  **Multipart Form Fields**

  .. list-table::
     :header-rows: 1

     * - Field
       - Type
       - Required
       - Description
     * - ``files``
       - file[]
       - Yes
       - ``.docx``, ``.pdf``, or ``.rtf`` files to analyze. Include this form field once per uploaded file.
     * - ``public_dashboard_link``
       - boolean
       - No
       - Whether to create and return a ``dashboard_link`` for each uploaded file. Defaults to ``false``.

  **Example Request**

  .. code-block:: http

    POST https://file-external.api.pangram.com/ HTTP/1.1
    x-api-key: your_api_key_here
    Content-Type: multipart/form-data; boundary=...

    --...
    Content-Disposition: form-data; name="files"; filename="document.docx"
    Content-Type: application/octet-stream

    <file bytes>
    --...
    Content-Disposition: form-data; name="public_dashboard_link"

    true
    --...--

  **Example cURL**

  .. code-block:: bash

    curl -s -X POST https://file-external.api.pangram.com \
      -H "x-api-key: $PANGRAM_API_KEY" \
      -F "files=@path/to/first.docx" \
      -F "files=@path/to/second.pdf" \
      -F "public_dashboard_link=true"

  **Example Response**

  .. code-block:: json

    [
      {
        "filename": "document.docx",
        "text": "Extracted document text...",
        "version": "3.3",
        "headline": "Human Written",
        "prediction": "We believe this is human-written",
        "prediction_short": "Human",
        "fraction_ai": 0.0,
        "fraction_ai_assisted": 0.0,
        "fraction_human": 1.0,
        "num_ai_segments": 0,
        "num_ai_assisted_segments": 0,
        "num_human_segments": 1,
        "windows": [],
        "dashboard_link": "https://www.pangram.com/history/123e4567-e89b-12d3-a456-426614174000"
      }
    ]

  **Errors**

  - ``400 Bad Request`` - The multipart request is missing a file or includes invalid form data.
  - ``401 Unauthorized`` - The ``x-api-key`` is missing or invalid.
  - ``402 Payment Required`` - The account has insufficient credits.
  - ``413 Payload Too Large`` - The upload exceeds the maximum supported file size.
  - ``415 Unsupported Media Type`` - The uploaded file type is not supported.
  - ``422 Unprocessable Entity`` - The ``files`` field is missing, the form data is invalid, or Pangram could not extract valid text from the uploaded file.
  - ``500 Internal Server Error`` - There was an error processing the upload.

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
