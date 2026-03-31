from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
# Load the summarization pipeline
# Approach 1: Direct summarization (newer versions)
print("Attempting with 'summarization' task...")
#summarizer = pipeline("text2text-generation", model="facebook/bart-large-cnn")
#summary_key = 'generated_text'
print("Loading model...")
model_name = "facebook/bart-large-cnn"



# Text to summarize
text =  """
Hugging Face is a company and open-source platform that provides tools and models for natural language processing (NLP). It has become a central hub for the ML community, offering a wide range of pre-trained models that can be easily used or fine-tuned for specific applications. Key aspects of Hugging Face include the Transformers library, Model Hub, Datasets library, and Tokenizers library. Hugging Face democratizes access to powerful ML models, making it easier for developers and researchers to build and deploy applications.
"""
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
inputs = tokenizer(
    text,
    return_tensors="pt",
    max_length=1024,
    truncation=True
)

with torch.no_grad():
    summary_ids = model.generate(
        inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        max_length=50,
        min_length=25,
        num_beams=4,
        length_penalty=2.0,
        early_stopping=True
    )

# Summarize the text
summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True) #summarizer(text, max_length=50, min_length=25, do_sample=False)

print("Original Text:")
print(text)
print("\nSummary:")
print(summary)