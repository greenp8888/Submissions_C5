Submit your assignments here.
from transformers import pipeline
import gradio as gr

sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

sentiment_pipeline("This is great!")

def analyze_sentiment(text):
    result = sentiment_pipeline(text)
    label = result[0]["label"]
    print(label)
    return f"{label} "

demo = gr.Interface(
    fn=analyze_sentiment,
    inputs=gr.Textbox(lines=3, placeholder="Enter text here..."),
    outputs=gr.Textbox(label="Sentiment"),
    title="Sentiment Analyzer",
    description="Enter any text and get its sentiment",
)
demo.launch(debug=False)
