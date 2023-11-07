checkfor.ai Quickstart Guide
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
    score = result['likelihood']

Make an async request
~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from checkforai import TextClassifier

    classifier = TextClassifier()
    result = await classifier.predict_async(text)


