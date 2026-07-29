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

### Discover available models

Model availability is specific to your API key. Use `list_models()` instead of
hard-coding a model catalog:

```
available_models = pangram_client.list_models()
print(available_models)  # e.g., ["default", "pangram-4"]
```

The returned list preserves the server's model order and only includes models
that your API key can currently use. The keyword-only `model` argument on text
and bulk requests is temporarily optional for backward compatibility. Omitting
it selects Pangram's abstract default and emits a `DeprecationWarning`.
Explicitly pass `model="default"` or `model="pangram-4"` in new code. After
September 30, 2026, callers will be required to select a model explicitly.

### Make a request

Main prediction method (AI-assistance detection and segment-level analysis):
```
from pangram import Pangram
pangram_client = Pangram()

result = pangram_client.predict(text, model="pangram-4")
stage = result['stage']  # "STAGE_SUCCESS" after predict() completes.
version = result['version']  # "4.0" for Pangram 4.

# Analysis with AI-assistance detection.
fraction_ai = result['fraction_ai']
fraction_ai_assisted = result['fraction_ai_assisted']
fraction_human = result['fraction_human']
num_ai_segments = result['num_ai_segments']

# Access individual window classifications
for window in result['windows']:
    label = window['label']  # "AI-Generated", "AI-Assisted", or "Human Written"
    ai_assistance_score = window['ai_assistance_score']
    confidence = window['confidence']  # A string: "High", "Medium", or "Low"
    is_humanized = window['is_humanized']
    humanizer_score = window['humanizer_score']  # 0.0-1.0
```
`predict()` submits to Pangram's async inference API and waits for the result before returning.
Use `predict(text, model="pangram-4", public_dashboard_link=True)` or
`predict_with_dashboard_link(text, model="pangram-4", timeout=300,
poll_interval=0.5)` to include a `dashboard_link` in the completed result.

Pangram 4 returns `version == "4.0"`. Every Pangram 4 window includes
`is_humanized` and `humanizer_score`. Pangram 4 uses the single
`"AI-Assisted"` window label rather than lightly/moderately assisted variants,
and `confidence` remains a string.

Results remain normal dictionaries. For typed applications, the package
exports `PredictionResult`, `PredictionWindow`, `BulkResultsPage`, and
`BulkResults` `TypedDict` contracts.

### Upload files

Use `predict_file()` or `predict_files()` when you want Pangram to extract text
from `.docx`, `.pdf`, or `.rtf` documents and create AI detection results.
Each result includes the extracted text, prediction fields, window-level
analysis, and the uploaded `filename`. Set `public_dashboard_link=True` to
include a `dashboard_link`.

File prediction currently uses Pangram's default model only.
`predict_file()` and `predict_files()` do not accept `model`.

```
from pangram import Pangram

pangram_client = Pangram()

result = pangram_client.predict_file(
    "path/to/document.docx",
    public_dashboard_link=True,
)

print(result["dashboard_link"])
print(result["prediction_short"])
print(result["filename"])
```

To upload multiple files in one request:

```
results = pangram_client.predict_files(
    ["path/to/first.docx", "path/to/second.pdf"],
    public_dashboard_link=True,
)

for result in results:
    print(result["dashboard_link"])
```

### Submit a Bulk API job

Use the Bulk API for asynchronous AI detection across many inputs.
Submit either a list of strings with `text` or a list of objects with `items`.
Item `id` values are optional customer IDs that are returned with item status
and results.

Bulk jobs are processed asynchronously. Completion time depends on the number
and length of submitted items and current system load. Use `get_bulk_status()`
or `wait_for_bulk()` to monitor progress.

```
from pangram import Pangram

pangram_client = Pangram()

bulk = pangram_client.submit_bulk(
    items=[
        {"id": "row-001", "text": "First text to analyze"},
        {"id": "row-002", "text": "Second text to analyze"},
    ],
    model="pangram-4",
)

bulk_id = bulk["bulk_id"]
status = pangram_client.wait_for_bulk(bulk_id, poll_interval=2)
results = pangram_client.get_bulk_results(bulk_id)

for item in results["items"]:
    if item["result"] is not None:
        print(item["id"], item["result"]["prediction_short"])

for failed in results["failed_items"]:
    print(failed["id"], failed["error"])
```

`model` is keyword-only and applies to the entire bulk job. During the
compatibility period, omitting it selects `"default"` and emits a
`DeprecationWarning`; after September 30, 2026, it will be required. Per-item
model selectors are not supported. Successful Pangram 4 item results use the
same version 4.0 and window schema described above.

Bulk jobs can also be inspected without waiting:

```
status = pangram_client.get_bulk_status(bulk_id)
items = pangram_client.get_bulk_items(bulk_id, offset=0, limit=100)
results_page = pangram_client.get_bulk_results_page(bulk_id, offset=0, limit=100)
```

For large jobs, use `get_bulk_results_page()` in a loop instead of `get_bulk_results()`
to process one page at a time without holding the full result set in memory:

```
offset = 0
limit = 1000

while True:
    page = pangram_client.get_bulk_results_page(bulk_id, offset=offset, limit=limit)
    for item in page["items"]:
        process(item)
    for failed in page["failed_items"]:
        handle_failure(failed)

    offset += limit
    if offset >= page["total_items"]:
        break
```

### Building Documentation

Install docs dependencies and build:
```
poetry install --with docs
cd docs && make html
```

Questions? Email [support@pangram.com](mailto:support@pangram.com)!
