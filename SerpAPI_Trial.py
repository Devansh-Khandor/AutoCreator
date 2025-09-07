# test_serpapi.py
import os, requests
from dotenv import load_dotenv
load_dotenv()
k = os.getenv("SERPAPI_KEY")
r = requests.get("https://serpapi.com/search.json",
                 params={"engine":"google","q":"OpenAI","api_key":k}, timeout=15)
print(r.status_code, r.json().get("error"))