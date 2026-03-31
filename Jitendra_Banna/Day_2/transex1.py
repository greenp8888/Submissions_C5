from transformers import pipeline
from PIL import Image
import requests
from io import BytesIO
# Load an image classification pipeline
classifier = pipeline("image-classification")

# Get an image from a URL (replace with your image URL)
url = "https://i.guim.co.uk/img/media/327aa3f0c3b8e40ab03b4ae80319064e401c6fbc/377_133_3542_2834/master/3542.jpg?width=1200&height=1200&quality=85&auto=format&fit=crop&s=34d32522f47e4a67286f9894fc81c863"
response = requests.get(url, timeout=30)
response.raise_for_status()
# image = Image.open(requests.get(url, stream=True).raw)
image = Image.open(BytesIO(response.content))

# Classify the image
predictions = classifier(image)

print("Image Classification Results:")
for prediction in predictions:
    print(f"- {prediction['label']}: {prediction['score']:.2f}")