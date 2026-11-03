Image 1.0, Flash, and video
===========================

The current ``pangram-sdk`` Python client exposes text, document-extraction,
bulk, and plagiarism methods. This guide calls the image and video REST APIs
with ``requests``; it does not require or introduce new SDK methods.

Do not pass image model selectors to ``Pangram.predict()`` or
``Pangram.submit_bulk()``. ``Pangram.list_models()`` discovers text models.
The ``predict_file()`` and ``predict_files()`` methods extract text from
documents; they do not classify images or videos.

Authentication and polling
--------------------------

Set ``PANGRAM_API_KEY`` to your API key. Image and video use the same
authentication header. Each task requires the same key for submission and polling.

The following helper waits for an accepted task. Keep its task ID if a local
timeout occurs and continue polling that task.

.. code-block:: python

    import os
    import time

    import requests

    image_headers = {"x-api-key": os.environ["PANGRAM_API_KEY"]}

    def wait_for_task(base_url, task_path, task_id, *, headers, timeout=600):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            response = requests.get(
                f"{base_url}{task_path}/{task_id}",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            if result["stage"] == "STAGE_SUCCESS":
                return result
            if result["stage"] == "STAGE_FAILED":
                raise RuntimeError(result["error"])
            time.sleep(0.5)
        raise TimeoutError(f"Task {task_id} is still processing; keep polling it.")

Image 1.0 and Image Flash 1.0
-----------------------------

Both models use ``https://image.external-api.pangram.com`` with
``POST /v1/tasks`` and ``GET /v1/tasks/{task_id}``.

.. list-table:: Image model selection
   :header-rows: 1
   :widths: 35 35 30

   * - Model
     - Request ``model``
     - Result ``version``
   * - Pangram Image 1.0
     - ``pangram-image-1``
     - ``Pangram Image 1.0``
   * - Pangram Image Flash 1.0
     - ``pangram-image-flash-1``
     - ``Pangram Image Flash 1.0``

The ``model`` field is optional on the REST endpoint, but set it explicitly to
choose Image 1.0 or Flash. The current production default is Image 0.2.
Availability can differ by environment; an unavailable model returns HTTP 503.

Submit one base64-encoded image per task. The decoded image limit is 32 MiB,
and the full JSON body limit is 128 MiB.

.. code-block:: python

    import base64
    from pathlib import Path

    image_base_url = "https://image.external-api.pangram.com"
    image_model = "pangram-image-1"  # Or "pangram-image-flash-1".

    response = requests.post(
        f"{image_base_url}/v1/tasks",
        headers=image_headers,
        json={
            "image_b64": base64.b64encode(Path("image.png").read_bytes()).decode("ascii"),
            "model": image_model,
        },
        timeout=60,
    )
    response.raise_for_status()
    image_task_id = response.json()["task_id"]
    image_result = wait_for_task(
        image_base_url, "/v1/tasks", image_task_id, headers=image_headers
    )
    print(image_result["prediction"], image_result["version"])

The image ``prediction`` is one of ``AI Detected``, ``Likely AI``, ``Unsure``,
``Likely No AI``, ``No AI``, or ``Partially AI``. Results also include
``ai_likelihood``, ``confidence``, ``detection_source``, ``heatmap``,
``metadata``, and ``thumbnail``.

When validated AI provenance determines a result, ``detection_source`` is
``c2pa`` and model-specific scores, confidence, version, and heatmap can be
``null``. Handle nullable fields rather than assuming every successful task
contains model output.

Video uploads
-------------

Upload an MP4, MOV, or WebM file as ``multipart/form-data`` with a single
``file`` field. Customers do not need to host the file or create an S3 URL.

.. code-block:: python

    video_base_url = "https://video.external-api.pangram.com"
    video_headers = {"x-api-key": os.environ["PANGRAM_API_KEY"]}

    with open("clip.mp4", "rb") as video:
        response = requests.post(
            f"{video_base_url}/v1/video/tasks",
            headers=video_headers,
            files={"file": ("clip.mp4", video, "video/mp4")},
            timeout=(10, 300),
        )
    response.raise_for_status()
    video_task_id = response.json()["task_id"]
    video_result = wait_for_task(
        video_base_url, "/v1/video/tasks", video_task_id, headers=video_headers
    )
    print(video_result["headline"], video_result["prediction_short"])

Let ``requests`` set the multipart Content-Type and its boundary.

Optional form fields are ``sampling_fps`` (default 3, range 0.1–24),
``hmm_smoothing`` (default false), and ``detailed_labels`` (default false).
The effective sampling rate is capped by the video's native frame rate.
For example, pass ``data={"hmm_smoothing": "true", "detailed_labels": "true"}``
alongside ``files`` to enable both options where available.

Video limits and results
~~~~~~~~~~~~~~~~~~~~~~~~

* One file per request, up to 500 MiB (524,288,000 bytes).
* Up to 360 sampled frames: approximately two minutes at the default 3 FPS.
  Lower sampling rates can accommodate longer videos, up to the ten-minute
  source-duration ceiling. Exceeding limits fails the task; the API does not
  automatically trim the uploaded video.
* Poll with the same key. Completed task results are retained for 24 hours.

The default response schema is ``1.1``. Use ``headline`` and ``prediction``
for display; ``prediction_short`` is ``no_ai``, ``mixed``, ``ai``, or ``unsure``.
``frames_processed`` and ``total_frames`` provide progress when available.

Successful responses include ``source.duration_ms``, the sampling settings,
frame scores, segments, and duration fractions. The ``version`` field identifies
the frame model (``Pangram Image Flash 1.0``); it is separate from
``schema_version``. Explicit ``?response_version=1.0`` on the polling URL returns
the legacy presentation.

Billing and retry behavior
--------------------------

Image tasks bill one image per successful task at the account's image API rate.

The default video rate is USD 0.05 per second of inspected source duration,
rounded up to a whole second. A 3.042-second video bills four seconds (USD 0.20);
a 60.001-second video bills 61 seconds (USD 3.05). Lower sampling FPS does not
reduce billable source duration. Failed tasks are not charged.

Image and video submissions do not accept an idempotency key. Each new POST
creates another task and can incur another charge. After receiving a task ID,
poll that task rather than submit the media again because polling timed out.

Request errors use an ``error`` object with ``error``, ``error_code``, and
``retryable``. A processing failure is returned by GET with HTTP 200 and
``stage == "STAGE_FAILED"``; the helper above handles that case.

HTTP 401 indicates missing or invalid credentials; 402 indicates insufficient
API funds; 403 indicates a key that does not own the task; 404 indicates an
unknown or expired task; 413 indicates an oversized upload; 422 indicates an
invalid request; 429 indicates a request rate limit; and 503 indicates an
unavailable feature or service.
