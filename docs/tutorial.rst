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

.. code:: python

    from pangram import Pangram

    pangram_client = Pangram()
    result = pangram_client.predict(text)
    # Score in range [0, 1] where 0 is human-written and 1 is AI-generated.
    score = result['ai_likelihood']

Make a batch request
~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from pangram import Pangram

    text_batch = ["text1", "text2"]

    pangram_client = Pangram()
    results = pangram_client.batch_predict(text_batch)
    for result in results:
        text = result["text"]
        score = result["ai_likelihood"]

Batch Inference
~~~~~~~~~~~~~~~~
Batch inference has significantly higher throughput, but can incur some startup latency especially if
multiple batch requests are sent at once. Use the single inference endpoint if latency is a strong requirement.
Use the batch inference endpoint if operating on multiple inputs at once.

Check for Plagiarism
~~~~~~~~~~~~~~~~~~~

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

The plagiarism detection response includes:
- Whether plagiarism was detected
- List of plagiarized content with source URLs
- Total number of sentences checked
- List of plagiarized sentences
- Percentage of text that was plagiarized

