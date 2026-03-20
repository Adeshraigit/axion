from pydantic import BaseModel, Field


class ProfileResponse(BaseModel):
    user_id: str
    full_name: str = ""
    linkedin_url: str | None = None
    github_url: str | None = None
    resume_text: str | None = None
    resume_file_name: str | None = None
    resume_uploaded_at: str | None = None
    hindsight_synced_at: str | None = None
    onboarding_completed_at: str | None = None


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = None
    linkedin_url: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=500)
    resume_text: str | None = Field(default=None, max_length=8000)
    mark_onboarding_complete: bool = False