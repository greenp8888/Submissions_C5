
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

client = OpenAI(api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )  #putting spaces do lead to error, so be careful while writing the key in .env file

completion = client.chat.completions.create(
  model="gemini-3-flash-preview",
  messages=[
    {"role": "developer", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of India."}
  ]
)

print(completion.choices[0].message.content) #You can only get the output you want by using .content at the end, otherwise you will get the whole response which is in json format.
