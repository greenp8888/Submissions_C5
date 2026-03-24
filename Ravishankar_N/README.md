Submit your assignments here.
import gradio as gr

def analyze_sentiment(text):
    if not text.strip():
        return "Please enter some text!"
    
    result = sentiment_pipeline(text)[0]
    
    label = result['label']
    score = result['score'] * 100  # convert to percentage
    
    # Make the output friendly and readable
    emoji = "😊" if label == "POSITIVE" else "😞"
    
    output = f"{emoji} Sentiment: {label}\n📊 Confidence: {score:.2f}%"
    return output

# Build the Gradio Interface
demo = gr.Interface(
    fn=analyze_sentiment,                          # function to call
    inputs=gr.Textbox(
        lines=4,
        placeholder="Type something here... e.g. I love this!",
        label="Your Text"
    ),
    outputs=gr.Textbox(label="Sentiment Result"),
    title="💬 Sentiment Analyser",
    description="Type any sentence and find out if it's Positive or Negative!",
    examples=[
        ["I absolutely love this product, it changed my life!"],
        ["This is the worst experience I have ever had."],
        ["Today was just an okay kind of day, nothing special."]
    ]
)

demo.launch()
