from datetime import datetime, timezone
from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.auth import AuthContext, get_current_user
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest
from app.services.memory.hindsight_service import hindsight_service
from app.services.repositories.supabase_repository import supabase_repo

router = APIRouter()


async def _retain_profile_snapshot(user_id: str, profile: dict) -> bool:
    parts: list[str] = []
    if profile.get("full_name"):
        parts.append(f"Name: {profile['full_name']}")
    if profile.get("linkedin_url"):
        parts.append(f"LinkedIn: {profile['linkedin_url']}")
    if profile.get("github_url"):
        parts.append(f"GitHub: {profile['github_url']}")
    if profile.get("resume_text"):
        parts.append(f"Resume details: {str(profile['resume_text'])[:3000]}")

    if not parts:
        return False

    retained = await hindsight_service.retain_memory(
        user_id,
        "User profile context snapshot. " + " | ".join(parts),
        memory_type="world_fact",
    )
    return retained


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(
    user_id: str,
    auth: AuthContext = Depends(get_current_user),
) -> ProfileResponse:
    if user_id != auth.user_id:
        raise HTTPException(status_code=403, detail="Forbidden: user mismatch")

    profile = await supabase_repo.get_profile(user_id, auth.access_token)
    return ProfileResponse(**profile)


@router.patch("/{user_id}", response_model=ProfileResponse)
async def update_profile(
    user_id: str,
    payload: ProfileUpdateRequest,
    auth: AuthContext = Depends(get_current_user),
) -> ProfileResponse:
    if user_id != auth.user_id:
        raise HTTPException(status_code=403, detail="Forbidden: user mismatch")

    update_payload: dict[str, str | None] = {}
    if payload.full_name is not None:
        update_payload["full_name"] = payload.full_name.strip()
    if payload.linkedin_url is not None:
        update_payload["linkedin_url"] = payload.linkedin_url.strip() or None
    if payload.github_url is not None:
        update_payload["github_url"] = payload.github_url.strip() or None
    if payload.resume_text is not None:
        update_payload["resume_text"] = payload.resume_text.strip() or None

    if payload.mark_onboarding_complete:
        update_payload["onboarding_completed_at"] = datetime.now(timezone.utc).isoformat()

    if update_payload:
        profile = await supabase_repo.update_profile(user_id, auth.access_token, update_payload)
        synced = await _retain_profile_snapshot(user_id, profile)
        if synced:
            profile = await supabase_repo.update_profile(
                user_id,
                auth.access_token,
                {"hindsight_synced_at": datetime.now(timezone.utc).isoformat()},
            )
    else:
        profile = await supabase_repo.get_profile(user_id, auth.access_token)

    return ProfileResponse(**profile)


@router.post("/{user_id}/resume", response_model=ProfileResponse)
async def upload_resume_pdf(
    user_id: str,
    resume_file: UploadFile = File(...),
    auth: AuthContext = Depends(get_current_user),
) -> ProfileResponse:
    if user_id != auth.user_id:
        raise HTTPException(status_code=403, detail="Forbidden: user mismatch")

    if resume_file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Resume must be a PDF file")

    file_bytes = await resume_file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Resume file is too large (max 10MB)")

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="PDF parsing dependency is missing. Install pypdf.") from exc

    try:
        reader = PdfReader(BytesIO(file_bytes))
        extracted = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    except Exception as exc:  # pragma: no cover - defensive parsing guard
        raise HTTPException(status_code=400, detail="Unable to parse resume PDF") from exc

    if not extracted:
        raise HTTPException(status_code=400, detail="No readable text found in resume PDF")

    profile = await supabase_repo.update_profile(
        user_id,
        auth.access_token,
        {
            "resume_text": extracted,
            "resume_file_name": resume_file.filename,
            "resume_uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    await hindsight_service.retain_memory(
        user_id,
        "User uploaded resume PDF. Resume details: " + extracted[:3000],
        memory_type="world_fact",
    )
    synced = await _retain_profile_snapshot(user_id, profile)
    if synced:
        profile = await supabase_repo.update_profile(
            user_id,
            auth.access_token,
            {"hindsight_synced_at": datetime.now(timezone.utc).isoformat()},
        )

    return ProfileResponse(**profile)