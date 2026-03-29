from transformers import pipeline

# RAG Day 2 - 4 assignments 
https://drive.google.com/file/d/1Bpgw4qipyteyRGgeFd2SRKUc1wgyl4yn/view?usp=sharing

sentiment_analyzer = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')
def get_sentiment(text):
  """Analyzes the sentiment of the given text."""
  result = sentiment_analyzer(text)[0]
  return f"Label: {result['label']}, Score: {result['score']:.4f}"

# Gradio UI
import gradio as gr
# Create the Gradio interface
iface = gr.Interface(fn=get_sentiment, inputs="text", outputs="text", 
# Launch the interface
iface.launch()
