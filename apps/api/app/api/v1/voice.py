from pydantic import BaseModel
from fastapi import APIRouter

from app.services.voice.voice_service import voice_service

router = APIRouter()


class STTRequest(BaseModel):
    audio_base64: str


class STTResponse(BaseModel):
    transcript: str


@router.post("/transcribe", response_model=STTResponse)
async def transcribe(payload: STTRequest) -> STTResponse:
    transcript = await voice_service.speech_to_text(payload.audio_base64)
    return STTResponse(transcript=transcript)
