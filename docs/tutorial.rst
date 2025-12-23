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

    from pangram import Pangram

    my_api_key = ''  # Fill this in with your API key.
    pangram_client = Pangram(api_key=my_api_key)

Make a request
~~~~~~~~~~~~~~

Main prediction
~~~~~~~~~~~~~~~~~~~~~
Returns detailed analysis with AI-assistance detection and segment-level metrics

.. code:: python

    from pangram import Pangram

    pangram_client = Pangram()
    result = pangram_client.predict(text)
    # V3 analysis with AI-assistance detection
    fraction_ai = result['fraction_ai']
    fraction_ai_assisted = result['fraction_ai_assisted']
    fraction_human = result['fraction_human']
    num_ai_segments = result['num_ai_segments']
    # Access individual window classifications
    for window in result['windows']:
        label = window['label']
        ai_assistance_score = window['ai_assistance_score']
        confidence = window['confidence']

Short prediction
~~~~~~~~~~~~~~~~~
Single Pangram model prediction, cuts off text at 512 tokens

.. code:: python

    from pangram import Pangram

    pangram_client = Pangram()
    result = pangram_client.predict_short(text)
    # Score in range [0, 1] where 0 is human-written and 1 is AI-generated.
    score = result['ai_likelihood']

Check for Plagiarism
~~~~~~~~~~~~~~~~~~~~~

The plagiarism detection API helps you identify potential plagiarism by comparing text against a vast database of online content:

.. code:: python

    from pangram import Pangram

    pangram_client = Pangram()

    text = "Text to check for plagiarism"
    result = pangram_client.check_plagiarism(text)

    if result['plagiarism_detected']:
        print(f"Plagiarism detected! {result['percent_plagiarized']}% of the text may be plagiarized.")
        for content in result['plagiarized_content']:
            print(f"Found match at {content['source_url']}")
            print(f"Matched text: {content['matched_text']}")

The plagiarism detection response includes

- Whether plagiarism was detected
- List of plagiarized content with source URLs
- Total number of sentences checked
- List of plagiarized sentences
- Percentage of text that was plagiarized

Deprecated Methods
~~~~~~~~~~~~~~~~~~~

The following methods are deprecated and will be removed by April 1st, 2026:

- ``predict_extended()`` - Use ``predict()`` instead
- ``batch_predict()`` - Use ``predict()`` instead
- ``predict_sliding_window()`` - Use ``predict()`` instead