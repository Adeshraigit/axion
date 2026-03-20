from __future__ import annotations

import random
import httpx

from app.core.config import get_settings


class JobProvider:
    # Hybrid provider: external API first, deterministic mock fallback.
    def __init__(self) -> None:
        self.settings = get_settings()

    async def fetch_jobs(self, skills: list[str], preferred_role: str | None = None) -> list[dict]:
        if self.settings.jobs_api_url and self.settings.jobs_api_key:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    response = await client.get(
                        self.settings.jobs_api_url,
                        headers={"Authorization": f"Bearer {self.settings.jobs_api_key}"},
                        params={"skills": ",".join(skills), "limit": 20},
                    )
                    response.raise_for_status()
                    payload = response.json()
                    return payload.get("jobs", [])
            except Exception:
                pass

        # Deterministic mock data for local/dev and resilient fallback.
        random.seed("|".join(sorted(skills)) + (preferred_role or "general"))
        roles = [preferred_role] if preferred_role else ["Frontend Intern", "Backend Intern", "Full Stack Intern"]
        jobs = []
        for idx in range(20):
            title = roles[idx % len(roles)]
            jobs.append(
                {
                    "title": title,
                    "company": f"Company {idx + 1}",
                    "location": random.choice(["Remote", "Bangalore", "Mumbai", "Pune"]),
                    "url": f"https://jobs.example.com/{idx+1}",
                }
            )
        return jobs


job_provider = JobProvider()
