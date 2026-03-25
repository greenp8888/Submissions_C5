import gradio as gr
from transformers import pipeline

# 1. Initialize the pipeline outside the function so it only loads once
sentiment_model = pipeline("sentiment-analysis")

# 2. Define the function that Gradio will execute
def analyze_sentiment(text):
    # Basic validation
    if not text or not text.strip():
        return "Please enter some text.", "0.00%", "No input provided."

    # Get the prediction
    result = sentiment_model(text)[0]

    label = result["label"]
    score = round(result["score"] * 100, 2)

    # Friendly explanation
    if label.upper() == "POSITIVE":
        explanation = "The text sounds positive in tone."
    else:
        explanation = "The text sounds negative in tone."

    # Return values for multiple UI components
    return label, f"{score}%", explanation

# 3. Create the interface
with gr.Blocks(theme=gr.themes.Soft(), title="Sentiment Analyzer") as demo:
    gr.Markdown(
        """
        # Sentiment Analyzer
        Enter a sentence below and detect whether the sentiment is **positive** or **negative**.
        """
    )

    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(
                label="Enter text",
                placeholder="Type a sentence to analyze...",
                lines=4
            )

            with gr.Row():
                analyze_btn = gr.Button("Analyze", variant="primary")
                clear_btn = gr.Button("Clear")

            gr.Examples(
                examples=[
                    ["I absolutely loved the workshop today. It was very clear and practical."],
                    ["This was a disappointing experience and I would not recommend it."],
                    ["The interface looks good, but the app feels a bit slow sometimes."]
                ],
                inputs=text_input
            )

        with gr.Column():
            sentiment_output = gr.Textbox(label="Predicted Sentiment")
            confidence_output = gr.Textbox(label="Confidence")
            explanation_output = gr.Textbox(label="Explanation", lines=3)

    analyze_btn.click(
        fn=analyze_sentiment,
        inputs=text_input,
        outputs=[sentiment_output, confidence_output, explanation_output]
    )

    clear_btn.click(
        fn=lambda: ("", "", "", ""),
        inputs=[],
        outputs=[text_input, sentiment_output, confidence_output, explanation_output]
    )

# 4. Launch
if __name__ == "__main__":
    demo.launch()
