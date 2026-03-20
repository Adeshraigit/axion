from __future__ import annotations

import base64
from io import BytesIO

from app.core.config import get_settings


class VoiceService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def text_to_speech(self, text: str) -> str | None:
        # Encode synthesized bytes as base64 for simple frontend playback.
        if not self.settings.elevenlabs_api_key:
            return None

        try:
            from elevenlabs.client import ElevenLabs

            client = ElevenLabs(api_key=self.settings.elevenlabs_api_key)
            audio_bytes = b"".join(
                client.text_to_speech.convert(
                    voice_id=self.settings.elevenlabs_voice_id,
                    output_format="mp3_22050_32",
                    text=text,
                    model_id="eleven_multilingual_v2",
                )
            )
            return base64.b64encode(audio_bytes).decode("utf-8")
        except Exception:
            return None

    async def speech_to_text(self, audio_base64: str) -> str:
        # Placeholder STT path for v1; replace with ElevenLabs STT endpoint integration.
        try:
            _ = BytesIO(base64.b64decode(audio_base64.encode("utf-8")))
            return "[Transcribed audio input]"
        except Exception:
            return ""


voice_service = VoiceService()
