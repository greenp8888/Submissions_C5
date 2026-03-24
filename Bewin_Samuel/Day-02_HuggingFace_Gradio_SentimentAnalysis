def get_sentiment(sentiment):
    from transformers import pipeline
    sentimentAnalyzer = pipeline("sentiment-analysis")
    output = sentimentAnalyzer(sentiment, do_sample=True)
    return output[0]['label']

def debug(output):
    print(len(output))
    print(output)

def create_interface():
  import gradio as gr
  demo = gr.Interface(fn=get_sentiment, inputs="text", outputs="label")
  demo.launch(debug=True)

def main():
  create_interface()

main()
