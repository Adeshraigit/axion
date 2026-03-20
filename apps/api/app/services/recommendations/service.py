from __future__ import annotations

from collections import Counter

from app.services.jobs.firecrawl_enrichment import firecrawl_enrichment_service
from app.services.jobs.provider import job_provider
from app.services.memory.hindsight_service import hindsight_service
from app.services.repositories.supabase_repository import supabase_repo


async def _infer_preferences(user_id: str, token: str) -> str | None:
    # Infer role preference from application history.
    apps = await supabase_repo.list_applications(user_id, token)
    if not apps:
        return None
    role_counts = Counter(app["role"] for app in apps)
    return role_counts.most_common(1)[0][0]


async def generate_daily_recommendations(
    user_id: str,
    skills: list[str],
    observations: list[str],
    token: str,
) -> list[dict]:
    preferred_role = await _infer_preferences(user_id, token)
    profile = await supabase_repo.get_profile(user_id, token)

    memory_query_parts = [preferred_role or "software internship", "skill gaps", "career goals"]
    if profile.get("linkedin_url"):
        memory_query_parts.append("linkedin")
    if profile.get("github_url"):
        memory_query_parts.append("github")

    memory_context = await hindsight_service.recall_memory(user_id, " ".join(memory_query_parts))
    jobs = await job_provider.fetch_jobs(skills=skills, preferred_role=preferred_role)
    user_skill_set = {skill.lower() for skill in skills}

    top_ten = []
    for index, job in enumerate(jobs[:10]):
        base_score = 85 - (index * 3)
        if preferred_role and preferred_role.lower() in job["title"].lower():
            base_score += 7

        scraped_markdown = ""
        if index < 5 and job.get("url"):
            scraped_markdown = await firecrawl_enrichment_service.scrape_job_markdown(job["url"])

        expected_skills = firecrawl_enrichment_service.infer_expected_skills(
            scraped_markdown,
            job.get("title", ""),
        )
        missing_skills = [item for item in expected_skills if item.lower() not in user_skill_set]
        matched_skills = [item for item in expected_skills if item.lower() in user_skill_set]

        if expected_skills:
            coverage = int((len(matched_skills) / len(expected_skills)) * 100)
            base_score = int((base_score + coverage) / 2)
        base_score -= min(12, len(missing_skills) * 2)

        reasoning = [f"Matches your skill profile: {', '.join(skills[:3])}"]
        if observations:
            reasoning.append(f"Aligned with behavior insight: {observations[0]}")
        if preferred_role:
            reasoning.append(f"Consistent with your application trend: {preferred_role}")
        if memory_context:
            reasoning.append(f"Uses memory context: {memory_context[0][:120]}")

        if expected_skills:
            profile_match = (
                f"Matched {len(matched_skills)}/{len(expected_skills)} expected skills for this role"
            )
        else:
            profile_match = "Limited role requirements available; match estimated from profile and history"

        top_ten.append(
            {
                **job,
                "match_score": max(0, min(100, base_score)),
                "reasoning": " | ".join(reasoning),
                "expected_skills": expected_skills,
                "missing_skills": missing_skills,
                "profile_match": profile_match,
            }
        )

    await supabase_repo.upsert_recommendations(user_id, top_ten, token)
    return top_ten
