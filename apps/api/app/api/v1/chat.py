from fastapi import APIRouter, Depends, HTTPException

from app.agents.career_mentor import career_mentor_agent
from app.core.auth import AuthContext, get_current_user
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.memory.hindsight_service import hindsight_service
from app.services.recommendations.service import generate_daily_recommendations
from app.services.repositories.supabase_repository import supabase_repo
from app.services.voice.voice_service import voice_service

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    auth: AuthContext = Depends(get_current_user),
) -> ChatResponse:
    if payload.user_id != auth.user_id:
        raise HTTPException(status_code=403, detail="Forbidden: user mismatch")

    # 1) Ensure user profile context exists.
    await supabase_repo.get_or_create_profile(payload.user_id, auth.access_token)

    # 2) Retain user interaction for long-term memory.
    await hindsight_service.retain_memory(payload.user_id, payload.message)

    # 3) Recall relevant memories and reflect for observations.
    recalled = await hindsight_service.recall_memory(payload.user_id, payload.message)
    reflection = await hindsight_service.reflect_on_memory(
        payload.user_id,
        "Summarize behavior patterns and practical career insights.",
    )
    observations = reflection.get("observations", []) if isinstance(reflection, dict) else []

    # 4) Ask agent to produce contextual mentorship.
    response_text = await career_mentor_agent.respond(
        user_id=payload.user_id,
        message=payload.message,
        memory_context=recalled,
        observations=observations,
    )

    # 5) Trigger recommendations refresh using current state.
    skills = await supabase_repo.list_skills(payload.user_id, auth.access_token)
    await generate_daily_recommendations(
        user_id=payload.user_id,
        skills=[item["name"] for item in skills],
        observations=observations,
        token=auth.access_token,
    )

    # 6) Optional voice output.
    audio_base64 = await voice_service.text_to_speech(response_text) if payload.include_voice else None

    next_steps = [
        "Apply to 2-3 matching internships today",
        "Upgrade one project bullet with metrics",
        "Practice one interview topic for 30 minutes",
    ]
    return ChatResponse(
        response=response_text,
        observations=observations[:3],
        next_steps=next_steps,
        audio_base64=audio_base64,
    )
