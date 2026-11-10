Account APIs
============

Requires SDK 1.2.0 or later. Set ``PANGRAM_API_KEY`` before running this example.

.. code-block:: python

   from decimal import Decimal
   from pangram import Pangram

   client = Pangram()
   balance = client.get_balance()
   available_usd = Decimal(balance["available_balance_usd"])
   usage = client.get_usage()  # Current UTC month; use month="2026-10" for another month.
   limits = client.get_limits()

Response fields and examples are documented in the public API reference:

* `Credit balance <https://docs.pangram.com/api-reference/balance>`_: account credits.
* `Monthly usage <https://docs.pangram.com/api-reference/usage>`_: usage for the API key.
* `QPS limit <https://docs.pangram.com/api-reference/limits>`_: account request rate.

See :doc:`api/pangram` for method signatures and exceptions, and the
`Python SDK reference <https://docs.pangram.com/sdk/python#account-read-errors>`_
for timeout and error-handling details.
