from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.memory.hindsight_service import hindsight_service
from app.services.recommendations.service import generate_daily_recommendations
from app.services.repositories.supabase_repository import supabase_repo


class SchedulerService:
    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler(timezone="UTC")
        self._started = False

    def start(self) -> None:
        if self._started:
            return

        # Run every day at 08:00 UTC for all known users.
        self._scheduler.add_job(self._daily_job, "cron", hour=8, minute=0, id="daily_recommendations")
        self._scheduler.start()
        self._started = True

    def shutdown(self) -> None:
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False

    def _daily_job(self) -> None:
        # Synchronous scheduler callback; delegate async work per user.
        import asyncio

        async def _run() -> None:
            users = await supabase_repo.list_user_ids_for_recommendations()
            for user_id in users:
                skills = await supabase_repo.list_skills_service(user_id)
                reflection = await hindsight_service.reflect_on_memory(
                    user_id, "Generate top behavior observations for today job matching."
                )
                observations = reflection.get("observations", []) if isinstance(reflection, dict) else []
                recommendations = await generate_daily_recommendations(
                    user_id=user_id,
                    skills=[item["name"] for item in skills],
                    observations=observations,
                    token=supabase_repo.service_role_key,
                )

        asyncio.run(_run())


scheduler_service = SchedulerService()
