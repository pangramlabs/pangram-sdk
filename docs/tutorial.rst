Checkfor.ai Quickstart Guide
===================================

Usage
-----

Install `checkforai`
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    pip install checkforai

Add your API key
~~~~~~~~~~~~~~~~

Either export it as an environment variable:

.. code-block:: bash

    export CHECKFORAI_API_KEY=<your API key>

Or pass it directly to the constructor:

.. code:: python

    my_api_key = ''  # Fill this in with your API key.
    classifier = TextClassifier(api_key=my_api_key)

Make a request
~~~~~~~~~~~~~~

.. code:: python

    from checkforai import TextClassifier

    classifier = TextClassifier()
    result = classifier.predict(text)
    # Score in range [0, 1] where 0 is human-written and 1 is AI-generated.
    score = result['ai_likelihood']

Make a batch request
~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from checkforai import TextClassifier

    text_batch = ["text1", "text2"]

    classifier = TextClassifier()
    results = classifier.batch_predict(text_batch)
    for result in results:
        text = result["text"]
        score = result["ai_likelihood"]

Batch Inference
~~~~~~~~~~~~~~~~
Each GPU takes about 20 seconds to spin up and spins down after 1 minute of inactivity. Therefore, to maximize our throughput we want to make sure the GPUs have a consistent stream of data to process.

Every request has some level of overhead. To reduce this overhead, we ask that you send your requests in batches of up to 1024 requests if possible.

We expect a latency of around 10 seconds for classifying 1024 texts. When a new machine is starting up, this can take up to 30 seconds.

Sometimes, when a machine is starting up, the request will time out after 30 seconds. Please retry the request - it should be a lot faster after the machine is warm.

You may send multiple concurrent requests at the same time, but please limit this to 20 concurrent open requests.

