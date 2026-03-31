
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  #putting spaces do lead to error, so be careful while writing the key in .env file

completion = client.chat.completions.create(
  model="gpt-5.4-nano",
  messages=[
    {"role": "developer", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of India."}
  ]
)

print(completion.choices[0].message)
