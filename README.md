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

Questions? Email [support@pangram.com](mailto:support@pangram.com)!
