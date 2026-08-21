Image Detection API
===================

The production Image API detects AI-generated images asynchronously. Submit
one base64-encoded image to create a task, then poll that task until its stage
is ``STAGE_SUCCESS`` or ``STAGE_FAILED``.

The Python package does not currently expose a dedicated image client method.
Use ``requests`` with the same Pangram API key used by the SDK.

Authentication
--------------

Set your API key in the environment:

.. code-block:: bash

   export PANGRAM_API_KEY=<your API key>

Send it in the ``x-api-key`` header on every request. A task can only be read
with the same API key that created it.

Submit an image
---------------

.. http:post:: https://image.external-api.pangram.com/v1/tasks

   :<json string image_b64: Required base64 image bytes or a base64 data URL.
   :>json string task_id: Server-generated UUID for the asynchronous task.

   The decoded image can be at most 32 MiB, and the complete JSON request body
   can be at most 128 MiB. The endpoint accepts one image per task; there is no
   public bulk-image endpoint.

   **Python**

   .. code-block:: python

      import base64
      import os
      from pathlib import Path

      import requests

      image_b64 = base64.b64encode(Path("image.png").read_bytes()).decode("ascii")
      response = requests.post(
          "https://image.external-api.pangram.com/v1/tasks",
          headers={"x-api-key": os.environ["PANGRAM_API_KEY"]},
          json={"image_b64": image_b64},
          timeout=30,
      )
      response.raise_for_status()
      task_id = response.json()["task_id"]

   **cURL**

   .. code-block:: bash

      base64 < image.png | tr -d '\n' \
        | jq -Rs '{image_b64: .}' \
        | curl -sS \
            -H 'content-type: application/json' \
            -H "x-api-key: $PANGRAM_API_KEY" \
            --data-binary @- \
            https://image.external-api.pangram.com/v1/tasks

   Successful admission returns ``202 Accepted``:

   .. code-block:: json

      {
        "task_id": "8db93921-df98-4edf-ae1d-8dd5839cd473"
      }

Poll the task
-------------

.. http:get:: https://image.external-api.pangram.com/v1/tasks/(string:task_id)

   :>json string task_id: UUID returned when the task was created.
   :>json string stage: Processing or terminal task stage.
   :>json string prediction: ``AI Detected``, ``Human``, ``Mixed``, or ``Unsure``. Present on success.
   :>json float ai_likelihood: Model score from 0.0 to 1.0, or null for a C2PA detection. Present on success.
   :>json string confidence: ``Low``, ``Medium``, or ``High``, or null for a C2PA detection. Present on success.
   :>json string detection_source: ``model`` or ``c2pa``. Present on success.
   :>json string version: Image model version, or null for a C2PA detection. Present on success.
   :>json object heatmap: Patch-level ``grid`` and input-pixel ``patch_stride``, or null for a C2PA detection. Present on success.
   :>json object metadata: C2PA, software, and camera metadata. Present on success.
   :>json object thumbnail: Metadata-stripped JPEG ``data_url``, ``width``, and ``height``, or null. Present on success.
   :>json object error: Typed ``error``, ``error_code``, and ``retryable`` values. Present on failure.

   Processing stages are ``STAGE_IMAGE_SAFETY``,
   ``STAGE_IMAGE_INFERENCE``, and ``STAGE_IMAGE_FINALIZING``. Terminal stages
   are ``STAGE_SUCCESS`` and ``STAGE_FAILED``.

   .. code-block:: python

      import os
      import time

      import requests

      headers = {"x-api-key": os.environ["PANGRAM_API_KEY"]}

      while True:
          response = requests.get(
              f"https://image.external-api.pangram.com/v1/tasks/{task_id}",
              headers=headers,
              timeout=30,
          )
          response.raise_for_status()
          result = response.json()
          if result["stage"] in {"STAGE_SUCCESS", "STAGE_FAILED"}:
              break
          time.sleep(0.5)

Success response
----------------

.. code-block:: json

   {
     "task_id": "8db93921-df98-4edf-ae1d-8dd5839cd473",
     "stage": "STAGE_SUCCESS",
     "prediction": "Human",
     "ai_likelihood": 0.0002,
     "confidence": "High",
     "detection_source": "model",
     "version": "Pangram Image 0.2",
     "heatmap": {
       "grid": [[0.1, 0.9]],
       "patch_stride": 16
     },
     "metadata": {
       "c2pa": {
         "present": false,
         "validation_state": null,
         "claim_generator_info": null,
         "issuer": null,
         "actions": []
       },
       "software": [],
       "camera": null
     },
     "thumbnail": {
       "data_url": "data:image/jpeg;base64,<base64 JPEG>",
       "width": 256,
       "height": 171
     }
   }

The thumbnail's longest edge is at most 256 pixels. It is re-encoded as JPEG
without source EXIF, XMP, or C2PA metadata and returned inline as a data URL.
Images are never upscaled.

For model detections, ``heatmap.grid`` contains patch-level scores and
``patch_stride`` gives their spacing in input pixels. For C2PA detections,
``ai_likelihood``, ``confidence``, ``version``, and ``heatmap`` are null.

Failed tasks and request errors
-------------------------------

Safety-blocked tasks never expose a model result, heatmap, or thumbnail:

.. code-block:: json

   {
     "task_id": "8db93921-df98-4edf-ae1d-8dd5839cd473",
     "stage": "STAGE_FAILED",
     "error": {
       "error": "The image could not be processed because it failed a safety check.",
       "error_code": "unsafe_image",
       "retryable": false
     }
   }

Immediate HTTP errors return the same typed ``error`` object without a task ID
or stage. Relevant status codes include:

* ``400`` for malformed JSON or invalid base64.
* ``401`` for a missing or invalid API key.
* ``402`` for insufficient credits.
* ``403`` when the API key cannot access the task.
* ``404`` when the task does not exist.
* ``413`` when the body or decoded image exceeds its size limit.
* ``422`` when a required field is missing or the JSON body does not match the
  request schema.
* ``429`` when the API key exceeds its configured rate limit.
* ``500`` for an unexpected service error.
* ``503`` when image processing is temporarily unavailable.

Use ``error.retryable`` to decide whether retrying may succeed.
An image that passes request validation but cannot be decoded during processing
can fail asynchronously with ``error_code`` set to ``invalid_image``.
