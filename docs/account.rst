Account balance, usage, and limits
==================================

These read-only endpoints use ``https://text.external-api.pangram.com`` and
your existing ``x-api-key`` header. They also work with zero or negative
balances. They do not run inference, spend credits, or consume
the account's inference QPS allowance.

SDK 1.2.0 (unreleased) adds ``get_balance()``, ``get_usage()``, and
``get_limits()``. Set ``PANGRAM_API_KEY`` before running these examples.
Each method returns an ordinary dictionary with a public ``TypedDict``
contract: ``AccountBalance``, ``AccountUsage``, or ``AccountLimits``.

Balance
-------

Use ``GET /balance`` to read the billing account associated with the key.

.. code-block:: python

   from decimal import Decimal
   from pangram import Pangram

   client = Pangram()
   balance = client.get_balance()
   available_usd = Decimal(balance["available_balance_usd"])

Example response:

.. code-block:: json

   {
     "purchased_balance_usd": "10.00000",
     "subscription_included_balance_usd": "2.50000",
     "available_balance_usd": "12.50000"
   }

Amounts are USD decimal strings; use ``Decimal`` for calculations.
``purchased_balance_usd`` also includes non-subscription grants and adjustments.
``available_balance_usd`` is the sum of the two balances, and balances may be
negative. This is the committed credit balance, not a pending-request
reservation, invoice amount, or a universal number of remaining scans.

Balance is account-wide, so keys on the same billing account see the same
balance. Public reference: https://docs.pangram.com/api-reference/balance

Usage
-----

Use ``GET /usage`` for one calling key's recorded billable usage in one UTC
calendar month. The optional ``month`` parameter accepts ``YYYY-MM`` and
defaults to the current UTC month. A partial current month contains records
committed so far. Future months and query parameters other than ``month`` are
rejected with ``422``.

.. code-block:: python

   from pangram import Pangram

   client = Pangram()
   usage = client.get_usage(month="2026-10")  # Omit month for the current UTC month.

Example response:

.. code-block:: json

   {
     "month": "2026-10",
     "total_requests": 10,
     "total_cost_usd": "0.750000"
   }

``total_requests`` counts recorded external billable rows across products, not
all HTTP attempts or bulk parent submissions. ``total_cost_usd`` is a USD
decimal string summing recorded charges, not an invoice or credit purchase
total. Historical missing or zero charges are not recalculated at today's
prices. An unused month returns zero requests and ``"0.000000"`` cost.

Usage is restricted to the calling key. Other keys on the account and keys
replaced by rotation have separate histories. Account IDs, key IDs, date
ranges, daily breakdowns, and product filters are not supported. Use the
dashboard for account-wide history.

Public reference: https://docs.pangram.com/api-reference/usage

QPS limit
---------

Use ``GET /limits`` to read the billing account's configured inference QPS
limit. Keys on the account share that limit for each metered endpoint.

.. code-block:: python

   from pangram import Pangram

   client = Pangram()
   limits = client.get_limits()

Example response:

.. code-block:: json

   {"qps_limit": 2.5}

``qps_limit`` is a JSON number, including fractional values, or ``null`` when
no account QPS limit is configured. It is not a live remaining-request counter
or a promise of available service capacity. No bulk or concurrency limits are
returned. Public reference: https://docs.pangram.com/api-reference/limits

Errors and read budgets
-----------------------

Each method accepts a positive finite keyword-only ``timeout`` in seconds,
defaulting to 10. It makes one HTTP request, disables redirects, and does not
automatically retry. Invalid local input raises ``ValueError``; HTTP,
transport, and malformed-response failures raise ``PangramRequestError``.
The exception exposes ``status_code`` and a numeric ``retry_after`` delay in
seconds. On a rate limit, wait for that delay before making another read.

All three endpoints share a separate account-read budget. The current
safeguards allow 60 reads per key per minute, 300 reads across all keys per
minute, and two concurrent reads per gateway process. These are process-local
protective limits, not a distributed account-wide quota or a guaranteed
allowance. Respect ``Retry-After`` on ``429`` and avoid polling continuously.

Responses use ``Cache-Control: no-store``. Avoid shared caching of account data.

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - Status
     - Meaning
   * - 401
     - Missing, malformed, inactive, revoked, or otherwise invalid key/account.
   * - 422
     - Invalid/future usage month or unsupported usage query parameter.
   * - 429
     - Account-read rate or concurrency limit; observe ``Retry-After``.
   * - 503
     - Account lookup unavailable or timed out. A later read can be retried.

Use ``/balance`` for available credits; ``/usage`` reports consumption.
