from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthContext, get_current_user
from app.schemas.dashboard import DashboardResponse, JobRecommendation, ProjectItem, SkillItem
from app.services.memory.hindsight_service import hindsight_service
from app.services.recommendations.service import generate_daily_recommendations
from app.services.repositories.supabase_repository import supabase_repo

router = APIRouter()


async def _build_dashboard_response(user_id: str, token: str) -> DashboardResponse:
    profile = await supabase_repo.get_profile(user_id, token)
    skills = [SkillItem(**skill) for skill in await supabase_repo.list_skills(user_id, token)]
    projects = [ProjectItem(**project) for project in await supabase_repo.list_projects(user_id, token)]
    recs = [
        JobRecommendation(**job)
        for job in await supabase_repo.list_recommendations(user_id, token)
    ]
    applications_summary = await supabase_repo.get_applications_summary(user_id, token)

    return DashboardResponse(
        profile={
            "full_name": profile.get("full_name"),
            "linkedin_url": profile.get("linkedin_url"),
            "github_url": profile.get("github_url"),
            "resume_text": profile.get("resume_text"),
            "resume_file_name": profile.get("resume_file_name"),
            "resume_uploaded_at": profile.get("resume_uploaded_at"),
            "hindsight_synced_at": profile.get("hindsight_synced_at"),
        },
        skills=skills,
        projects=projects,
        applications_summary=applications_summary,
        daily_recommendations=recs,
    )


@router.get("/{user_id}", response_model=DashboardResponse)
async def get_dashboard(
    user_id: str,
    auth: AuthContext = Depends(get_current_user),
) -> DashboardResponse:
    if user_id != auth.user_id:
        raise HTTPException(status_code=403, detail="Forbidden: user mismatch")

    return await _build_dashboard_response(user_id, auth.access_token)


@router.post("/{user_id}/recommendations/refresh", response_model=DashboardResponse)
async def refresh_recommendations(
    user_id: str,
    auth: AuthContext = Depends(get_current_user),
) -> DashboardResponse:
    if user_id != auth.user_id:
        raise HTTPException(status_code=403, detail="Forbidden: user mismatch")

    skills = await supabase_repo.list_skills(user_id, auth.access_token)
    reflection = await hindsight_service.reflect_on_memory(
        user_id,
        "Summarize profile strengths, behavior patterns, and role fit guidance.",
    )
    observations = reflection.get("observations", []) if isinstance(reflection, dict) else []

    await generate_daily_recommendations(
        user_id=user_id,
        skills=[item.get("name", "") for item in skills if item.get("name")],
        observations=[item for item in observations if isinstance(item, str)],
        token=auth.access_token,
    )

    return await _build_dashboard_response(user_id, auth.access_token)
