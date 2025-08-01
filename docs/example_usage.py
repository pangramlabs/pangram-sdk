"""
Example usage of the Pangram Text SDK with improved type documentation.

This example demonstrates how the improved return type documentation
helps with IDE support and code clarity.
"""

from pangram.text_classifier import PangramText, ClassificationResult, PlagiarismResult

# Initialize the classifier
classifier = PangramText(api_key="your-api-key-here")

# Example 1: Single text classification
# The return type is now clearly documented as ClassificationResult
result: ClassificationResult = classifier.predict("This is a sample text to classify.")

# Now you get better IDE support - you can see the exact fields available:
print(f"AI Score: {result['ai_score']}")
print(f"Human Score: {result['human_score']}")
print(f"Classification: {result['classification']}")
print(f"Confidence: {result['confidence']}")

# Example 2: Batch classification
# The return type is List[ClassificationResult]
batch_results = classifier.batch_predict([
    "First text to classify",
    "Second text to classify",
    "Third text to classify"
])

# Each item in the list is a ClassificationResult
for i, result in enumerate(batch_results):
    print(f"Text {i+1}: {result['classification']} (confidence: {result['confidence']:.2f})")

# Example 3: Plagiarism check
# The return type is PlagiarismResult with detailed field documentation
plagiarism_result: PlagiarismResult = classifier.check_plagiarism("Text to check for plagiarism")

# You can access the well-documented fields:
if plagiarism_result['plagiarism_detected']:
    print(f"Plagiarism detected! {plagiarism_result['percent_plagiarized']:.1f}% of text is plagiarized")
    print(f"Found {len(plagiarism_result['plagiarized_sentences'])} plagiarized sentences")
else:
    print("No plagiarism detected")

# Example 4: Dashboard link
# The return type is DashboardResult (extends ClassificationResult with dashboard_url)
dashboard_result = classifier.predict_with_dashboard_link("Text for dashboard analysis")
print(f"Dashboard URL: {dashboard_result['dashboard_url']}")
print(f"Classification: {dashboard_result['classification']}")