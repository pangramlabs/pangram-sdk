Image and video detection
=========================

SDK 1.1.0 adds native image and video methods to ``Pangram``. The existing
text, document-extraction, bulk, and plagiarism methods keep their behavior.
Use ``predict_image()`` for images and ``predict_video()`` for videos;
``predict_file()`` and ``predict_files()`` continue to extract text from documents.

Create a client
---------------

Set ``PANGRAM_API_KEY`` or pass ``api_key`` to the constructor. The SDK uses
that key for both submission and polling.

.. code-block:: python

    from pangram import Pangram

    client = Pangram()  # Reads PANGRAM_API_KEY.

Image detection
---------------

Select an image model explicitly:

.. list-table:: Image model selection
   :header-rows: 1
   :widths: 35 35 30

   * - Model
     - ``model`` argument
     - Example result ``version``
   * - Pangram Image 1
     - ``pangram-image-1``
     - ``Pangram Image 1.0``
   * - Pangram Image Flash 1
     - ``pangram-image-flash-1``
     - ``Pangram Image Flash 1.0``
   * - Pangram Image 0.2
     - ``pangram-image-0.2``
     - ``Pangram Image 0.2``

``model="default"`` follows the service default.
``list_models()`` discovers text models and does not list image models.

``pangram-image-1`` selects the Image 1 series, just as ``pangram-4`` selects
the Pangram 4 text series. Minor versions can change within the selected series
without changing the selector. Read the result's ``version`` field for the model
version used; it is ``None`` for an image result determined solely by validated
provenance.

.. code-block:: python

    result = client.predict_image("image.png", model="pangram-image-1")
    print(result["prediction"], result["ai_likelihood"])

    flash = client.predict_image("image.png", model="pangram-image-flash-1")
    print(flash["prediction"])

Inputs may be a file path, ``pathlib.Path``, raw bytes, or an open binary file.
The SDK encodes the bytes as base64 for the Image API. A string is a file path;
pass raw bytes instead of an already encoded base64 string. The image limit is
32 MiB. Caller-owned files stay open and are read from their current position.

``predict_image()`` submits once and polls, returning an ``ImageResult``
dictionary. Its ``prediction`` is ``AI Detected``, ``Likely AI``, ``Unsure``,
``Likely No AI``, ``No AI``, or ``Partially AI``.

Results include ``ai_likelihood``, ``confidence``, ``detection_source``,
``version``, ``heatmap``, ``metadata``, and ``thumbnail``. When validated AI
provenance determines the result, ``detection_source`` is ``c2pa`` and scores,
confidence, version, and heatmap can be ``None``. Handle these nullable fields.

Video uploads
-------------

Pass an MP4, MOV, or WebM file. The SDK streams uploads and uses the API's
processing defaults. Customers do not need to host the file or supply a URL.

.. code-block:: python

    result = client.predict_video("clip.mp4")
    print(result["headline"], result["prediction_short"])
    print(result["fraction_ai"], result["segments"])

A video may also be raw bytes or a seekable binary file. Supply ``filename``
when passing bytes or a stream without a filename:

.. code-block:: python

    from pathlib import Path

    result = client.predict_video(
        Path("clip.mp4").read_bytes(),
        filename="clip.mp4",
    )

Use a path for large videos to stream from disk. The SDK closes files it opens;
caller-owned streams remain open and are read from their current position.

``predict_video()`` returns a ``VideoResult`` dictionary using response schema
``1.1``. Its overall ``prediction_short`` is ``no_ai``, ``mixed``, ``ai``, or
``unsure``. Use ``headline`` and ``prediction`` for display.

Results include source duration and dimensions, sampled frames, timeline
segments, and duration fractions. The top-level ``version`` identifies the
frame model as ``image-flash-1``, or is ``None`` for a provenance-only result.
Frame-level prediction labels have their own vocabulary; segment labels can
include ``likely_human`` and ``likely_ai``.

* One file per request, up to 500 MiB (524,288,000 bytes).
* Frame analysis supports up to two minutes for videos at 3 FPS or higher.
  The API samples three frames per second, up to 360 sampled frames. For
  lower-frame-rate videos, it samples at the source frame rate.
* The API does not automatically trim the uploaded video. Files exceeding
  processing limits fail.
* Completed results are retained for 24 hours.

Submission, progress, and resuming
----------------------------------

Use separate submission and polling methods to persist the task ID or show
progress in your application:

.. code-block:: python

    task = client.submit_video("clip.mp4")
    task_id = task["task_id"]  # Persist this ID before waiting.

    status = client.get_video_status(task_id)
    print(status["stage"])
    result = client.wait_for_video(task_id, timeout=600)

Images have the matching ``submit_image(image, model=...)``,
``get_image_status(task_id)``, and ``wait_for_image(task_id)`` methods.
Status methods return processing, success, or failure dictionaries. Video
processing responses may include ``frames_processed`` and ``total_frames``.
Waiting and prediction methods raise ``MediaTaskError`` for failed tasks;
its ``task_id`` and ``error`` attributes preserve the API details.

``predict_image()`` defaults to a 300-second timeout and polls every 0.5 seconds.
``predict_video()`` defaults to 600 seconds and polls every second. The prediction
budget includes submission and polling. Separate submission methods default to
60 seconds for images and 300 seconds for video uploads. Status requests default
to ten seconds. Every method accepts a ``timeout`` override; wait and prediction
methods also accept ``poll_interval`` (minimum 0.1 seconds).

If polling times out, resume the accepted task rather than uploading again:

.. code-block:: python

    from pangram import MediaTaskTimeout

    try:
        result = client.predict_video("clip.mp4", timeout=60)
    except MediaTaskTimeout as error:
        # Save error.task_id if you want to resume later.
        result = client.wait_for_video(error.task_id, timeout=600)

The SDK retries polling after temporary transport errors and HTTP 429/5xx
responses, honoring numeric ``Retry-After`` delays. Other API failures raise
``MediaRequestError``, whose ``status_code`` is available when a response was
received. File-opening errors use Python's normal file exceptions.

Billing and retries
-------------------

Image tasks bill one image per successful task at the account's image API rate.
Video tasks bill USD 0.05 per second of inspected source duration, rounded up to
a whole second: 3.042 seconds costs USD 0.20 and 60.001 seconds costs USD 3.05.
Failed tasks are not charged.

Submissions do not support idempotency keys. The SDK never automatically retries
a submission. A transport error can leave its outcome unknown; submitting again
may create a second billable task. Once a task ID is available, use its status
or wait method instead of resubmitting the media.
