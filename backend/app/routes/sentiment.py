from fastapi import APIRouter, HTTPException

from app.services.sentiment.vader_service import VaderSentimentService

router = APIRouter(tags=["sentiment"])
service = VaderSentimentService()


@router.post("/sentiment/analyze")
def analyze_text(payload: dict | None = None):
    body = payload or {}
    text = body.get("text")
    if text is None and isinstance(body, str):
        text = body
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    return service.analyze_text(text)
