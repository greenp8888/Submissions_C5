import gradio as gr
from transformers import pipeline

# 1. Load the pipeline
# This will download the model to the Colab instance
pipe = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# 2. Define the prediction function
def predict_sentiment(text):
    # Get the model prediction
    results = pipe(text)[0] # This returns a dict like {'label': 'POSITIVE', 'score': 0.99}
    
    # FIXED: Using 'results' (the correct variable name)
    label = results['label']
    score = results['score'] * 100 

    # Logic for user-friendly display
    emoji = "😊" if label == "POSITIVE" else "😞"
    
    # Return a formatted string
    return f"### {emoji} Sentiment: {label}\n**Confidence:** {score:.2f}%"

# 3. Create the Gradio Interface
demo = gr.Interface(
    fn=predict_sentiment,
    inputs=gr.Textbox(placeholder="Enter a sentence here...", lines=2, label="Input Text"),
    # CHANGED: Using Markdown for the formatted string output
    outputs=gr.Markdown(label="Result"), 
    title="Sentiment Analyzer",
    description="Enter text to see if it is Positive or Negative. Powered by DistilBERT.",
    examples=["I love this MacBook shortcut!", "This model is confusing."]
)

# 4. Launch it
# share=True creates a public URL you can send to friends
demo.launch(share=True)
