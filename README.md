# checkfor.ai Python

### Usage
Install checkforai
```
pip install checkforai
```

##### Add your API key
Either export it as a variable.
```
export CHECKFORAI_API_KEY=<your API key>
```
Or pass it in to the constructor:
```
my_api_key = ''  # Fill this in with your API key.
classifier = TextClassifier(api_key=my_api_key)
```

##### Make a request
```
from checkforai import TextClassifier

classifier = TextClassifier()
result = classifier.predict(text)
# Score in range [0, 1] where 0 is human-written and 1 is AI-generated.
score = result['likelihood']
```

##### Make an async request
```
from checkforai import TextClassifier

classifier = TextClassifier()
result = await classifier.predict_async(text)
```

Questions? Email me at max@checkfor.ai!
