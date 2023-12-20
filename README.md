# Checkfor.ai Python

### Installation
```
pip install checkforai
```

### Add your API key
Either export it as a variable.
```
export CHECKFORAI_API_KEY=<your API key>
```
Or pass it in to the constructor:
```
my_api_key = ''  # Fill this in with your API key.
classifier = TextClassifier(api_key=my_api_key)
```

### Make a request
```
from checkforai import TextClassifier

classifier = TextClassifier()
result = classifier.predict(text)
# Score in range [0, 1] where 0 is human-written and 1 is AI-generated.
score = result['ai_likelihood']
```

### Make a batch request
```
from checkforai import TextClassifier

text_batch = ["abc", "def"]

classifier = TextClassifier()
results = classifier.batch_predict(text_batch)
for result in results:
    text = result['text']
    score = result['ai_likelihood']
```

Questions? Email me at max@checkfor.ai!
