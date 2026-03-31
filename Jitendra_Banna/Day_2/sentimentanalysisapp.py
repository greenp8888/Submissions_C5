from transformers import pipeline
import gradio as gr
#  Load the sentiment analysis pipeline
# Using distilbert-base-uncased-finetuned-sst-2-english (lightweight and accurate)
sentiment_model = pipeline("text-classification") #pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
#sentiment_model = pipeline(model='distilbert-base-uncased-finetuned-sst-2-english')
print("Loading sentiment analysis model...")
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

def get_sentiment(text):
    """
    Analyze sentiment of input text
    Returns: sentiment label and confidence score
    """
    result = sentiment_model(text)[0]
    return result['label'], result['score']

def analyze_sentiment(text):
    """
    Analyze sentiment of input text and return formatted result
    """
    if not text or text.strip() == "":
        return "⚠️ Please enter some text to analyze."
    
    # Get sentiment prediction
    result = sentiment_pipeline(text)[0]
    label = result['label']
    score = result['score']
    
    # Format the output based on sentiment
    if label == "POSITIVE":
        emoji = "😊"
        color_info = "Positive sentiment detected!"
    else:
        emoji = "😔"
        color_info = "Negative sentiment detected!"
    
    # Create formatted output
    output = f"""
    {emoji} **Sentiment Analysis Result** {emoji}
    
    **Text:** "{text}"
    
    **Sentiment:** {label} {emoji}
    
    **Confidence:** {score:.2%}
    
    {color_info}
    """
    
    return output

# Create the Gradio interface
demo = gr.Interface(
    fn=analyze_sentiment,
    inputs=gr.Textbox(
        label="Enter your text here", 
        placeholder="Type something like: 'I love this movie!' or 'This product is terrible...'",
        lines=3
    ),
    outputs=gr.Markdown(label="Sentiment Analysis Result"),
    title="🎭 Sentiment Analyzer",
    description="""
    ### Analyze the sentiment of any text!
    
    This app uses a Hugging Face transformer model (DistilBERT) fine-tuned on SST-2 dataset.
    It will tell you whether the text has a **positive** or **negative** sentiment.
    
    **Example inputs:**
    - "I absolutely love this product! It's amazing! 😊"
    - "This is the worst experience I've ever had. 😔"
    - "The movie was okay, nothing special."
    """,
    examples=[
        ["I love this movie! It's fantastic!"],
        ["This is terrible, I hate it."],
        ["The weather is beautiful today!"],
        ["I'm feeling okay, not great."],
        ["This is the best day ever!"],
    ],
    flagging_mode="auto"  # Automatically flag examples for debugging
)

# Launch the app
if __name__ == "__main__":
    demo.launch(share=True)  # share=True creates a public link
    
# Test the function
# test_text = "I love this product! It's amazing!"
# label, score = get_sentiment(test_text)
# print(f"Text: {test_text}")
# print(f"Sentiment: {label} (confidence: {score:.2f})")


