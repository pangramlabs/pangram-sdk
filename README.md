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
# Analysis with AI-assistance detection
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
`predict()` submits to Pangram's async AWS inference API and waits for the result before returning.

### Building Documentation

Install docs dependencies and build:
```
poetry install --with docs
cd docs && make html
```

Questions? Email [support@pangram.com](mailto:support@pangram.com)!
