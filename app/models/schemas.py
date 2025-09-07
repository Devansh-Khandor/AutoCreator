from pydantic import BaseModel, Field
from typing import List, Optional

class Topic(BaseModel):
    title: str
    angle: Optional[str] = None

class DraftVariant(BaseModel):
    variant: int
    text: str
    rationale: Optional[str] = None

class GenerateDraftRequest(BaseModel):
    topic: Topic
    platform: str = Field(default="linkedin")
    variants: int = Field(default=3, ge=1, le=5)

class GenerateDraftResponse(BaseModel):
    variants: List[DraftVariant]

class FinalizeRequest(BaseModel):
    text: str
    platform: str

class FinalizeResponse(BaseModel):
    final_text: str

class PublishRequest(BaseModel):
    platform: str
    text: str

class PublishResponse(BaseModel):
    ok: bool
    permalink: Optional[str] = None
    message: Optional[str] = None
