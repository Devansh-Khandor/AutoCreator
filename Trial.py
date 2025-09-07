from openai import OpenAI
import os

# make sure your .env is loaded
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    response = client.models.list()
    print("✅ OpenAI API key works! Available models:")
    for m in response.data[:5]:
        print("-", m.id)
except Exception as e:
    print("❌ Error:", e)
