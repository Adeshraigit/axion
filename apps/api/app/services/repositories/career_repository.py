from __future__ import annotations

from collections import Counter
from datetime import date
from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Application, DailyRecommendation, Project, Skill, UserProfile


class CareerRepository:
    async def ensure_default_profile(self, session: AsyncSession, user_id: str) -> None:
        profile = await session.get(UserProfile, user_id)
        if not profile:
            session.add(UserProfile(user_id=user_id))

        skills = await session.scalars(select(Skill).where(Skill.user_id == user_id))
        if not list(skills):
            session.add_all(
                [
                    Skill(user_id=user_id, name="React", level=3),
                    Skill(user_id=user_id, name="Python", level=2),
                ]
            )

        projects = await session.scalars(select(Project).where(Project.user_id == user_id))
        if not list(projects):
            session.add(Project(user_id=user_id, name="Portfolio Website", summary="Next.js personal portfolio with projects."))

        await session.commit()

    async def get_skills(self, session: AsyncSession, user_id: str) -> list[dict]:
        rows = (await session.scalars(select(Skill).where(Skill.user_id == user_id).order_by(Skill.created_at.desc()))).all()
        return [{"name": row.name, "level": row.level} for row in rows]

    async def get_projects(self, session: AsyncSession, user_id: str) -> list[dict]:
        rows = (await session.scalars(select(Project).where(Project.user_id == user_id).order_by(Project.created_at.desc()))).all()
        return [{"name": row.name, "summary": row.summary} for row in rows]

    async def get_applications(self, session: AsyncSession, user_id: str) -> list[dict]:
        rows = (
            await session.scalars(select(Application).where(Application.user_id == user_id).order_by(Application.created_at.desc()))
        ).all()
        return [
            {
                "id": row.id,
                "user_id": row.user_id,
                "company": row.company,
                "role": row.role,
                "status": row.status,
                "applied_on": row.applied_on,
            }
            for row in rows
        ]

    async def create_application(
        self,
        session: AsyncSession,
        user_id: str,
        company: str,
        role: str,
        status: str,
        applied_on: date | None,
    ) -> dict:
        row = Application(user_id=user_id, company=company, role=role, status=status, applied_on=applied_on)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return {
            "id": row.id,
            "user_id": row.user_id,
            "company": row.company,
            "role": row.role,
            "status": row.status,
            "applied_on": row.applied_on,
        }

    async def update_application_status(
        self,
        session: AsyncSession,
        user_id: str,
        application_id: str,
        status: str,
    ) -> dict | None:
        row = await session.get(Application, application_id)
        if not row or row.user_id != user_id:
            return None
        row.status = status
        await session.commit()
        await session.refresh(row)
        return {
            "id": row.id,
            "user_id": row.user_id,
            "company": row.company,
            "role": row.role,
            "status": row.status,
            "applied_on": row.applied_on,
        }

    async def get_applications_summary(self, session: AsyncSession, user_id: str) -> dict[str, int]:
        apps = await self.get_applications(session, user_id)
        counts = Counter(item["status"] for item in apps)
        return {
            "applied": counts.get("applied", 0),
            "interview": counts.get("interview", 0),
            "rejected": counts.get("rejected", 0),
            "offer": counts.get("offer", 0),
        }

    async def upsert_daily_recommendations(
        self,
        session: AsyncSession,
        user_id: str,
        jobs: list[dict],
        recommendation_date: date,
    ) -> None:
        existing = await session.scalar(
            select(DailyRecommendation).where(
                DailyRecommendation.user_id == user_id,
                DailyRecommendation.recommendation_date == recommendation_date,
            )
        )
        if existing:
            existing.jobs = jobs
        else:
            session.add(DailyRecommendation(user_id=user_id, recommendation_date=recommendation_date, jobs=jobs))
        await session.commit()

    async def get_latest_daily_recommendations(self, session: AsyncSession, user_id: str) -> list[dict]:
        row = await session.scalar(
            select(DailyRecommendation)
            .where(DailyRecommendation.user_id == user_id)
            .order_by(DailyRecommendation.recommendation_date.desc())
            .limit(1)
        )
        return row.jobs if row else []

    async def list_users_with_skills(self, session: AsyncSession) -> list[tuple[str, list[str]]]:
        user_ids = (await session.scalars(select(Skill.user_id).distinct())).all()
        results: list[tuple[str, list[str]]] = []
        for user_id in user_ids:
            skills = await self.get_skills(session, user_id)
            results.append((user_id, [item["name"] for item in skills]))
        return results


career_repository = CareerRepository()
