from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    # User id scopes both agent context and memory bank.
    user_id: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=5000)
    include_voice: bool = False


class ChatResponse(BaseModel):
    response: str
    observations: list[str] = []
    next_steps: list[str] = []
    audio_base64: str | None = None
