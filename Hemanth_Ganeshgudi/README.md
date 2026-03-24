Submit your assignments here.

24_Mar-2026 Gradio Huggingface
Imports: It imports gradio for the web interface and pipeline from transformers for the sentiment analysis model.
Model Initialization: A sentiment-analysis pipeline is created using a distilbert model. This model is loaded once when the script starts.
analyze_sentiment Function: This Python function takes a text input, passes it to the pre-trained sentiment_model to get a prediction, and then extracts the sentiment label (e.g., 'POSITIVE', 'NEGATIVE') and its score (confidence). It returns a formatted string with these results.
Gradio Interface (gr.Interface): This is where the web application is defined.
fn=analyze_sentiment links your Python function to the UI.
inputs=gr.Textbox(...) creates a text input box for the user.
outputs="text" specifies that the output will be displayed as text.
title and description provide information about the application.
demo.launch(): This command starts the Gradio web server, making your sentiment analyzer accessible via a local or public URL.
