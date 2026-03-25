import gradio as gr
from transformers import pipeline

classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

def sentiment(text):
    result = classifier(text)[0]
    return f"Sentiment: {result['label']}"

demo_tb = gr.Interface(
    fn=sentiment,
    inputs=gr.Textbox(label="Enter Text: "),
    outputs=gr.Textbox(label="Analysis: "),
    title="Sentiment Analysis"
)

demo_tb.launch()