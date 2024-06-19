Pangram Labs Quickstart Guide
===================================

Usage
-----

Install `pangram`
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    pip install pangram-sdk

Add your API key
~~~~~~~~~~~~~~~~

Either export it as an environment variable:

.. code-block:: bash

    export PANGRAM_API_KEY=<your API key>

Or pass it directly to the constructor:

.. code:: python

    my_api_key = ''  # Fill this in with your API key.
    classifier = PangramText(api_key=my_api_key)

Make a request
~~~~~~~~~~~~~~

.. code:: python

    from pangram import PangramText

    classifier = PangramText()
    result = classifier.predict(text)
    # Score in range [0, 1] where 0 is human-written and 1 is AI-generated.
    score = result['ai_likelihood']

Make a batch request
~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from pangram import PangramText

    text_batch = ["text1", "text2"]

    classifier = PangramText()
    results = classifier.batch_predict(text_batch)
    for result in results:
        text = result["text"]
        score = result["ai_likelihood"]

Batch Inference
~~~~~~~~~~~~~~~~
Batch inference has significantly higher throughput, but can incur some startup latency especially if
multiple batch requests are sent at once. Use the single inference endpoint if latency is a strong requirement.
Use the batch inference endpoint if operating on multiple inputs at once.

