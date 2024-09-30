# Pangram Labs Python Package

### Installation
```
pip install pangram-sdk
```

### Add your API key
Export it as a variable and import pangram directly:
```
export PANGRAM_API_KEY=<your API key>
```
```
from pangram import pangram
```
Or, if it's unavailable as an evironment variable, pass the api key directly as
an argument to the PangramText constructor.
```
from pangram import PangramText
my_api_key = ''  # Fill this in with your API key.
pangram_client = PangramText(api_key=my_api_key)
```

### Make a request
```
from pangram import pangram

result = pangram.predict(text)
# Score in range [0, 1] where 0 is human-written and 1 is AI-generated.
score = result['ai_likelihood']
```

### Make a batch request
```
from pangram import pangram

text_batch = ["abc", "def"]

results = pangram.batch_predict(text_batch)
for result in results:
    text = result['text']
    score = result['ai_likelihood']
```

Questions? Email [support@pangram.com](mailto:support@pangram.com)!
