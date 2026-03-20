from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthContext, get_current_user
from app.schemas.dashboard import DashboardResponse, JobRecommendation, ProjectItem, SkillItem
from app.services.repositories.supabase_repository import supabase_repo

router = APIRouter()


@router.get("/{user_id}", response_model=DashboardResponse)
async def get_dashboard(
    user_id: str,
    auth: AuthContext = Depends(get_current_user),
) -> DashboardResponse:
    if user_id != auth.user_id:
        raise HTTPException(status_code=403, detail="Forbidden: user mismatch")

    profile = await supabase_repo.get_profile(user_id, auth.access_token)
    skills = [SkillItem(**skill) for skill in await supabase_repo.list_skills(user_id, auth.access_token)]
    projects = [ProjectItem(**project) for project in await supabase_repo.list_projects(user_id, auth.access_token)]
    recs = [
        JobRecommendation(**job)
        for job in await supabase_repo.list_recommendations(user_id, auth.access_token)
    ]
    applications_summary = await supabase_repo.get_applications_summary(user_id, auth.access_token)

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
