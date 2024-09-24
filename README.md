# Pangram Labs Python Package

### Installation
```
pip install pangram-sdk
```

### Add your API key
Either export it as a variable and import ai_classifier directly.
```
export PANGRAM_API_KEY=<your API key>
```
```
from pangram import ai_classifier
```
Or pass an api key as an argument to the AIClassifier constructor.
```
from pangram import AIClassifier
my_api_key = ''  # Fill this in with your API key.
ai_classifier = AIClassifier(api_key=my_api_key)
```

### Make a request
```
from pangram import ai_classifier

result = ai_classifier.predict(text)
# Score in range [0, 1] where 0 is human-written and 1 is AI-generated.
score = result['ai_likelihood']
```

### Make a batch request
```
from pangram import ai_classifier

text_batch = ["abc", "def"]

results = ai_classifier.batch_predict(text_batch)
for result in results:
    text = result['text']
    score = result['ai_likelihood']
```

Questions? Email [support@pangram.com](mailto:support@pangram.com)!
