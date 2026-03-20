from __future__ import annotations

import re

import httpx

from app.core.config import get_settings

SKILL_KEYWORDS: dict[str, list[str]] = {
    "python": ["python", "django", "fastapi", "flask"],
    "javascript": ["javascript", "js", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "next.js", "nextjs"],
    "node": ["node", "node.js", "express"],
    "sql": ["sql", "postgres", "mysql", "sqlite"],
    "aws": ["aws", "amazon web services"],
    "docker": ["docker", "container"],
    "git": ["git", "github", "version control"],
    "system design": ["system design", "scalability", "distributed systems"],
}


class FirecrawlEnrichmentService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def scrape_job_markdown(self, url: str) -> str:
        if not self.settings.firecrawl_api_key:
            return ""

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    f"{self.settings.firecrawl_base_url}/scrape",
                    headers={
                        "Authorization": f"Bearer {self.settings.firecrawl_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "url": url,
                        "formats": ["markdown"],
                    },
                )
                response.raise_for_status()
                payload = response.json()
                data = payload.get("data", {}) if isinstance(payload, dict) else {}
                markdown = data.get("markdown", "") if isinstance(data, dict) else ""
                return markdown if isinstance(markdown, str) else ""
        except Exception:
            return ""

    def infer_expected_skills(self, text: str, title: str) -> list[str]:
        blob = f"{title}\n{text}".lower()
        expected: list[str] = []

        for skill, aliases in SKILL_KEYWORDS.items():
            if any(alias in blob for alias in aliases):
                expected.append(skill)

        title_tokens = re.findall(r"[a-zA-Z]+", title.lower())
        if "backend" in title_tokens and "python" not in expected:
            expected.append("python")
        if "frontend" in title_tokens and "react" not in expected:
            expected.append("react")
        if "full" in title_tokens and "javascript" not in expected:
            expected.append("javascript")

        return expected[:8]


firecrawl_enrichment_service = FirecrawlEnrichmentService()
