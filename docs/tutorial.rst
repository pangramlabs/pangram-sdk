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
~~~~~~~~~~~~~~~
Returns detailed analysis with AI-assistance detection and segment-level metrics
The SDK submits to Pangram's async inference API and waits for the completed result.

.. code:: python

    from pangram import Pangram

    pangram_client = Pangram()
    result = pangram_client.predict(text)
    stage = result['stage']  # "STAGE_SUCCESS" after predict() completes.

    # Analysis with AI-assistance detection.
    fraction_ai = result['fraction_ai']
    fraction_ai_assisted = result['fraction_ai_assisted']
    fraction_human = result['fraction_human']
    num_ai_segments = result['num_ai_segments']
    # Access individual window classifications
    for window in result['windows']:
        label = window['label']
        ai_assistance_score = window['ai_assistance_score']
        confidence = window['confidence']

Submit a Bulk API job
~~~~~~~~~~~~~~~~~~~~~
Use the Bulk API for asynchronous AI detection across many inputs. Submit either
a ``text`` list or an ``items`` list. ``items`` can include customer-defined
``id`` values that are returned with item status and results.

.. code:: python

    from pangram import Pangram

    pangram_client = Pangram()

    bulk = pangram_client.submit_bulk(items=[
        {"id": "row-001", "text": "First text to analyze"},
        {"id": "row-002", "text": "Second text to analyze"},
    ])

    bulk_id = bulk["bulk_id"]
    status = pangram_client.wait_for_bulk(bulk_id, poll_interval=2)
    results = pangram_client.get_bulk_results(bulk_id)

    for item in results["items"]:
        if item["result"] is not None:
            print(item["id"], item["result"]["prediction_short"])

    for failed in results["failed_items"]:
        print(failed["id"], failed["error"])

You can also inspect jobs without waiting:

.. code:: python

    status = pangram_client.get_bulk_status(bulk_id)
    items = pangram_client.get_bulk_items(bulk_id, offset=0, limit=100)
    results_page = pangram_client.get_bulk_results_page(bulk_id, offset=0, limit=100)

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
