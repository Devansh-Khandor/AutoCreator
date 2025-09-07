from atproto import Client
from app.config import settings
from app.models.schemas import PublishResponse

def publish_bluesky(text: str) -> PublishResponse:
    try:
        client = Client()
        client.login(settings.bluesky_handle, settings.bluesky_app_password)
        post = client.send_post(text=text)
        uri = getattr(post, "uri", None)
        return PublishResponse(ok=True, permalink=f"https://bsky.app/profile/{settings.bluesky_handle}/post/{uri.split('/')[-1] if uri else ''}")
    except Exception as e:
        return PublishResponse(ok=False, message=f"Bluesky error: {e}")

def export_linkedin_text(text: str) -> PublishResponse:
    # We return the text to the UI; user clicks "Copy" to clipboard.
    # (Publishing to LinkedIn API generally requires partner access.)
    return PublishResponse(ok=True, message="Copy this text and paste into LinkedIn composer.")
