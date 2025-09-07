from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    #OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    openai_fallback_model: str = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-5-nano")

    # SerpApi
    serpapi_key: str = os.getenv("SERPAPI_KEY", "")
    serpapi_engine: str = os.getenv("SERPAPI_ENGINE", "google")
    serpapi_location: str = os.getenv("SERPAPI_LOCATION", "India")
    serpapi_num: int = int(os.getenv("SERPAPI_NUM", "5"))

    # Bluesky
    bluesky_handle: str = os.getenv("BLUESKY_HANDLE", "")
    bluesky_app_password: str = os.getenv("BLUESKY_APP_PASSWORD", "")

settings = Settings()
