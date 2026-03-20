from pydantic import BaseModel


class SkillItem(BaseModel):
    name: str
    level: int


class ProjectItem(BaseModel):
    name: str
    summary: str


class JobRecommendation(BaseModel):
    title: str
    company: str
    location: str
    url: str
    match_score: int
    reasoning: str
    expected_skills: list[str] = []
    missing_skills: list[str] = []
    profile_match: str = ""


class DashboardResponse(BaseModel):
    profile: dict[str, str | None]
    skills: list[SkillItem]
    projects: list[ProjectItem]
    applications_summary: dict[str, int]
    daily_recommendations: list[JobRecommendation]
