import gradio as gr
from transformers import pipeline

# Load sentiment analysis pipeline
classifier = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)

def analyze_sentiment(text):
    if not text.strip():
        return "Enter some text bro."

    result = classifier(text)[0]

    return f"{result['label']} (confidence: {result['score']:.4f})"


demo = gr.Interface(
    fn=analyze_sentiment,
    inputs=gr.Textbox(
        lines=4,
        placeholder="Type something..."
    ),
    outputs=gr.Textbox(label="Sentiment"),
    title="😄 Sentiment Analyzer",
    description="Using Hugging Face pipeline (latest transformers)"
)


demo.launch()