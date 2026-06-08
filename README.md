# Pangram Labs Python Package

### Installation
```
pip install pangram-sdk
```

### Add your API key
Add your API key as an environment variable, or pass it directly to the
Pangram constructor.
```
export PANGRAM_API_KEY=<your API key>
```
```
from pangram import Pangram
# If the environment variable PANGRAM_API_KEY is set:
pangram_client = Pangram()

# Otherwise, pass the API key directly:
my_api_key = ''  # Fill this in with your API key.
pangram_client = Pangram(api_key=my_api_key)
```

### Make a request

Main prediction method (AI-assistance detection and segment-level analysis):
```
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
    label = window['label']  # e.g., "AI-Generated", "Moderately AI-Assisted"
    ai_assistance_score = window['ai_assistance_score']
    confidence = window['confidence']  # "High", "Medium", "Low"
```
`predict()` submits to Pangram's async inference API and waits for the result before returning.
Use `predict(text, public_dashboard_link=True)` or `predict_with_dashboard_link(text)` to include a `dashboard_link` in the completed result.

### Submit a Bulk API job

Use the Bulk API for asynchronous AI detection across many inputs.
Submit either a list of strings with `text` or a list of objects with `items`.
Item `id` values are optional customer IDs that are returned with item status
and results.

```
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
```

Bulk jobs can also be inspected without waiting:

```
status = pangram_client.get_bulk_status(bulk_id)
items = pangram_client.get_bulk_items(bulk_id, offset=0, limit=100)
results_page = pangram_client.get_bulk_results_page(bulk_id, offset=0, limit=100)
```

### Building Documentation

Install docs dependencies and build:
```
poetry install --with docs
cd docs && make html
```

Questions? Email [support@pangram.com](mailto:support@pangram.com)!
