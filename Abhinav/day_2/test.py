from transformers import pipeline
import gradio as gr

# model choice: `distilbert-base-uncased-finetuned-sst-2-english`
sentiment = pipeline("sentiment-analysis",
                     model="distilbert-base-uncased-finetuned-sst-2-english")

def classify(text):
    result = sentiment(text, truncation=True)[0]
    return f"{result['label']} (score {result['score']:.4f})"

iface = gr.Interface(fn=classify,
                     inputs=gr.Textbox(lines=3, placeholder="Type text here..."),
                     outputs="text",
                     title="Sentiment Analysis")
iface.launch()