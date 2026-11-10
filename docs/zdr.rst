Zero data retention (ZDR) text API
==================================

Use the ZDR endpoint when you need a completed text analysis without a saved
result that can be retrieved later:

.. code-block:: text

   POST https://text-zdr.external-api.pangram.com/

Authenticate with the same ``x-api-key`` header used by the other APIs. The
request accepts text and a model selector such as ``pangram-4``. Choose a model
enabled for your account and send the selector explicitly.

Python example
--------------

The SDK currently has no native ZDR prediction method. ``Pangram.predict()``
uses the standard async task API; it does not enable ZDR. Use this direct HTTP
call alongside the SDK instead. ``requests`` is already an SDK dependency.

.. code-block:: python

   import os
   import requests

   response = requests.post(
       "https://text-zdr.external-api.pangram.com/",
       headers={"x-api-key": os.environ["PANGRAM_API_KEY"]},
       json={"text": "The text to analyze", "model": "pangram-4"},
       timeout=(10, 610),
   )
   response.raise_for_status()
   result = response.json()
   if result["stage"] != "STAGE_SUCCESS":
       raise RuntimeError("ZDR analysis did not succeed")
   print(result["prediction_short"])

The timeout tuple gives connection establishment 10 seconds and allows 610
seconds of read inactivity while waiting for the response. It is not a total
wall-clock deadline or a guarantee of successful completion.

Unlike the standard async API, this call returns the terminal result directly;
do not poll a task ID. Successful results use the completed text response
fields documented in :doc:`api/rest`, including ``stage``, ``version``,
``prediction_short``, and ``windows``. A terminal analysis failure can return
``STAGE_FAILED``; check ``stage`` as well as the HTTP status.

Command-line example
--------------------

.. code-block:: bash

   curl --request POST \
     --url https://text-zdr.external-api.pangram.com/ \
     --connect-timeout 10 --max-time 610 \
     --header "Content-Type: application/json" \
     --header "x-api-key: $PANGRAM_API_KEY" \
     --data '{"text": "The text to analyze", "model": "pangram-4"}'

Content lifecycle and billing
-----------------------------

Submitted text and inference results are held transiently during processing.
The terminal result is consumed once, and the application removes the
task-owned content state as part of that handoff. Timeout and cancellation
paths attempt cleanup; expiry bounds abandoned task state.

There is no later result retrieval, dashboard history or public dashboard
link, webhook delivery, or bulk submission on this endpoint. Do not send
``public_dashboard_link=true``, ``webhook_delivery=true``, or end-user email
metadata.

Billing and operational metadata, such as request identifiers, timestamps,
input length, billable units, and cost, may still be retained. These records
are separate from submitted text and inference output. Your application is
responsible for its own request logs, response logs, and caches.

.. warning::

   Delivery is at most once. If the connection closes after the server has
   consumed the result, that result cannot be recovered. Retrying starts a new
   analysis and may incur another charge. Do not automatically retry the POST
   or fall back to the standard prediction API.

Strict-ZDR accounts
-------------------

The endpoint selects ZDR processing. An account's ``strict_zdr`` setting adds
an enforcement rule: its API keys receive ``403 Forbidden`` on standard text
and image inference routes. Using a regular key on the ZDR endpoint does not
change that key's account setting.

The standard ``GET /models`` route and ``Pangram.list_models()`` also reject
strict-ZDR keys. Use a selector approved for your account, or contact
``support@pangram.com`` to confirm it. :doc:`account` reads remain available
to strict-ZDR keys on the standard text API hostname.

Common HTTP errors include ``401`` for an invalid key, ``402`` for insufficient
credits, ``403`` for model access denial, ``422`` for invalid input, ``429``
for a submission rate limit, ``503`` for unavailable capacity, and ``504`` for
a synchronous timeout. No error makes a retry of an already accepted request
idempotent.

Public reference: https://docs.pangram.com/api-reference/zdr-api
