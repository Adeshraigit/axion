from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

import httpx

from app.core.config import get_settings
from app.schemas.application import ApplicationCreate, ApplicationUpdate


class SupabaseRepository:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.supabase_url.rstrip("/")
        self.anon_key = settings.supabase_anon_key
        self.service_role_key = settings.supabase_service_role_key

    def _headers(self, token: str, *, prefer: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def _service_headers(self, *, prefer: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    async def _get(
        self,
        table: str,
        token: str,
        params: dict[str, str],
        *,
        service_role: bool = False,
    ) -> list[dict[str, Any]]:
        url = f"{self.base_url}/rest/v1/{table}"
        headers = self._service_headers() if service_role else self._headers(token)
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else []

    async def _upsert(
        self,
        table: str,
        token: str,
        payload: list[dict[str, Any]],
        *,
        on_conflict: str,
        service_role: bool = False,
    ) -> None:
        url = f"{self.base_url}/rest/v1/{table}"
        headers = (
            self._service_headers(prefer="resolution=merge-duplicates")
            if service_role
            else self._headers(token, prefer="resolution=merge-duplicates")
        )
        params = {"on_conflict": on_conflict}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, params=params, json=payload)
            response.raise_for_status()

    async def _delete(
        self,
        table: str,
        token: str,
        filters: dict[str, str],
        *,
        service_role: bool = False,
    ) -> None:
        url = f"{self.base_url}/rest/v1/{table}"
        headers = self._service_headers() if service_role else self._headers(token)
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.delete(url, headers=headers, params=filters)
            response.raise_for_status()

    async def _insert(
        self,
        table: str,
        token: str,
        payload: dict[str, Any],
        *,
        return_representation: bool = False,
        service_role: bool = False,
    ) -> dict[str, Any] | None:
        url = f"{self.base_url}/rest/v1/{table}"
        prefer = "return=representation" if return_representation else None
        headers = (
            self._service_headers(prefer=prefer)
            if service_role
            else self._headers(token, prefer=prefer)
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            if return_representation:
                data = response.json()
                if isinstance(data, list) and data:
                    return data[0]
            return None

    async def _patch(
        self,
        table: str,
        token: str,
        filters: dict[str, str],
        payload: dict[str, Any],
    ) -> None:
        url = f"{self.base_url}/rest/v1/{table}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.patch(url, headers=self._headers(token), params=filters, json=payload)
            response.raise_for_status()

    async def get_or_create_profile(self, user_id: str, token: str) -> dict[str, Any]:
        rows = await self._get_profile_rows(user_id, token)
        if rows:
            return rows[0]

        try:
            await self._insert(
                "user_profiles",
                token,
                {
                    "user_id": user_id,
                    "full_name": "",
                },
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 409:
                raise

        rows = await self._get_profile_rows(user_id, token)
        return rows[0] if rows else {
            "user_id": user_id,
            "full_name": "",
            "linkedin_url": None,
            "github_url": None,
            "resume_text": None,
            "resume_file_name": None,
            "resume_uploaded_at": None,
            "hindsight_synced_at": None,
            "onboarding_completed_at": None,
        }

    async def _get_profile_rows(self, user_id: str, token: str) -> list[dict[str, Any]]:
        select_candidates = [
            "user_id,full_name,linkedin_url,github_url,resume_text,resume_file_name,resume_uploaded_at,hindsight_synced_at,onboarding_completed_at",
            "user_id,full_name,linkedin_url,github_url,resume_text,onboarding_completed_at",
            "user_id,full_name",
        ]

        last_error: httpx.HTTPStatusError | None = None
        for projection in select_candidates:
            try:
                return await self._get(
                    "user_profiles",
                    token,
                    {
                        "user_id": f"eq.{user_id}",
                        "select": projection,
                        "limit": "1",
                    },
                )
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 400:
                    last_error = exc
                    continue
                raise

        if last_error:
            raise last_error
        return []

    async def get_profile(self, user_id: str, token: str) -> dict[str, Any]:
        profile = await self.get_or_create_profile(user_id, token)
        return {
            "user_id": profile.get("user_id", user_id),
            "full_name": profile.get("full_name", "") or "",
            "linkedin_url": profile.get("linkedin_url"),
            "github_url": profile.get("github_url"),
            "resume_text": profile.get("resume_text"),
            "resume_file_name": profile.get("resume_file_name"),
            "resume_uploaded_at": profile.get("resume_uploaded_at"),
            "hindsight_synced_at": profile.get("hindsight_synced_at"),
            "onboarding_completed_at": profile.get("onboarding_completed_at"),
        }

    async def update_profile(self, user_id: str, token: str, payload: dict[str, Any]) -> dict[str, Any]:
        await self._patch(
            "user_profiles",
            token,
            {
                "user_id": f"eq.{user_id}",
            },
            payload,
        )
        return await self.get_profile(user_id, token)

    async def list_skills(self, user_id: str, token: str) -> list[dict[str, Any]]:
        return await self._get(
            "skills",
            token,
            {
                "user_id": f"eq.{user_id}",
                "select": "name,level",
                "order": "name.asc",
            },
        )

    async def list_projects(self, user_id: str, token: str) -> list[dict[str, Any]]:
        return await self._get(
            "projects",
            token,
            {
                "user_id": f"eq.{user_id}",
                "select": "name,summary",
                "order": "name.asc",
            },
        )

    async def list_applications(self, user_id: str, token: str) -> list[dict[str, Any]]:
        return await self._get(
            "applications",
            token,
            {
                "user_id": f"eq.{user_id}",
                "select": "id,user_id,company,role,status,applied_on",
                "order": "created_at.desc",
            },
        )

    async def create_application(
        self,
        user_id: str,
        payload: ApplicationCreate,
        token: str,
    ) -> dict[str, Any]:
        result = await self._insert(
            "applications",
            token,
            {
                "user_id": user_id,
                "company": payload.company,
                "role": payload.role,
                "status": payload.status,
                "applied_on": payload.applied_on,
            },
            return_representation=True,
        )
        return result or {
            "id": "",
            "user_id": user_id,
            "company": payload.company,
            "role": payload.role,
            "status": payload.status,
            "applied_on": payload.applied_on,
        }

    async def update_application(
        self,
        user_id: str,
        application_id: str,
        payload: ApplicationUpdate,
        token: str,
    ) -> None:
        update_payload: dict[str, Any] = {}
        if payload.status is not None:
            update_payload["status"] = payload.status

        if not update_payload:
            return

        await self._patch(
            "applications",
            token,
            {
                "id": f"eq.{application_id}",
                "user_id": f"eq.{user_id}",
            },
            update_payload,
        )

    async def get_applications_summary(self, user_id: str, token: str) -> dict[str, int]:
        apps = await self.list_applications(user_id, token)
        counts = Counter(item.get("status") for item in apps)
        return {
            "applied": counts.get("applied", 0),
            "interview": counts.get("interview", 0),
            "rejected": counts.get("rejected", 0),
            "offer": counts.get("offer", 0),
        }

    async def upsert_recommendations(
        self,
        user_id: str,
        recommendations: list[dict[str, Any]],
        token: str,
    ) -> None:
        await self._delete(
            "daily_recommendations",
            token,
            {
                "user_id": f"eq.{user_id}",
                "recommendation_date": f"eq.{date.today().isoformat()}",
            },
        )
        await self._insert(
            "daily_recommendations",
            token,
            {
                "user_id": user_id,
                "recommendation_date": date.today().isoformat(),
                "jobs": recommendations,
            },
        )

    async def list_recommendations(self, user_id: str, token: str) -> list[dict[str, Any]]:
        rows = await self._get(
            "daily_recommendations",
            token,
            {
                "user_id": f"eq.{user_id}",
                "select": "jobs",
                "order": "recommendation_date.desc",
                "limit": "1",
            },
        )
        if not rows:
            return []
        jobs = rows[0].get("jobs", [])
        return jobs if isinstance(jobs, list) else []

    async def list_user_ids_for_recommendations(self) -> list[str]:
        rows = await self._get(
            "user_profiles",
            self.service_role_key,
            {
                "select": "user_id",
            },
            service_role=True,
        )
        return [row.get("user_id") for row in rows if row.get("user_id")]

    async def list_skills_service(self, user_id: str) -> list[dict[str, Any]]:
        return await self._get(
            "skills",
            self.service_role_key,
            {
                "user_id": f"eq.{user_id}",
                "select": "name,level",
                "order": "name.asc",
            },
            service_role=True,
        )

    async def list_projects_service(self, user_id: str) -> list[dict[str, Any]]:
        return await self._get(
            "projects",
            self.service_role_key,
            {
                "user_id": f"eq.{user_id}",
                "select": "name,summary",
                "order": "name.asc",
            },
            service_role=True,
        )

    async def upsert_recommendations_service(
        self,
        user_id: str,
        recommendations: list[dict[str, Any]],
    ) -> None:
        await self._delete(
            "daily_recommendations",
            self.service_role_key,
            {
                "user_id": f"eq.{user_id}",
                "recommendation_date": f"eq.{date.today().isoformat()}",
            },
            service_role=True,
        )
        await self._insert(
            "daily_recommendations",
            self.service_role_key,
            {
                "user_id": user_id,
                "recommendation_date": date.today().isoformat(),
                "jobs": recommendations,
            },
            service_role=True,
        )


supabase_repo = SupabaseRepository()
