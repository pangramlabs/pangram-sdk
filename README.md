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

Basic prediction (scans first ~400 words of text, returns a single prediction):
```
from pangram import Pangram
pangram_client = Pangram()

result = pangram_client.predict_short(text)
# Score in range [0, 1] where 0 is human-written and 1 is AI-generated.
score = result['ai_likelihood']
```

Extended prediction (returns windows of AI/human text in a longer document)
```
from pangram import Pangram
pangram_client = Pangram()

result = pangram_client.predict_extended(text)
# Extended analysis with windowed results and detailed metrics
avg_score = result['avg_ai_likelihood']
max_score = result['max_ai_likelihood']
percent_ai = result['percent_ai']
```

Legacy predict method (calls predict_short internally):
```
from pangram import Pangram
pangram_client = Pangram()

result = pangram_client.predict(text)
# Score in range [0, 1] where 0 is human-written and 1 is AI-generated.
score = result['ai_likelihood']
```

### Make a batch request
```
from pangram import Pangram
pangram_client = Pangram()

text_batch = ["abc", "def"]

results = pangram_client.batch_predict(text_batch)
for result in results:
    text = result['text']
    score = result['ai_likelihood']
```

### Deprecated Methods

The following methods are deprecated and will be removed by April 1st, 2026:

- `predict_sliding_window()` - Use `predict_extended()` instead for better performance
- `predict_with_dashboard_link()` - Use `predict_extended` with the dashboard flag instead

Questions? Email [support@pangram.com](mailto:support@pangram.com)!
