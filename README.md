# Checkfor.ai Python

### Installation
```
pip install pangram
```

### Add your API key
Either export it as a variable.
```
export PANGRAM_API_KEY=<your API key>
```
Or pass it in to the constructor:
```
my_api_key = ''  # Fill this in with your API key.
classifier = PangramText(api_key=my_api_key)
```

### Make a request
```
from pangram import PangramText

classifier = PangramText()
result = classifier.predict(text)
# Score in range [0, 1] where 0 is human-written and 1 is AI-generated.
score = result['ai_likelihood']
```

### Make a batch request
```
from pangram import PangramText

text_batch = ["abc", "def"]

classifier = PangramText()
results = classifier.batch_predict(text_batch)
for result in results:
    text = result['text']
    score = result['ai_likelihood']
```

Questions? Email me at max@pangramlabs.com!
