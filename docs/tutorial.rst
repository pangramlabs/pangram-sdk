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

