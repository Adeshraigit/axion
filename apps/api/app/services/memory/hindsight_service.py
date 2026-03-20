from __future__ import annotations

import logging
import httpx
from app.core.config import get_settings


logger = logging.getLogger(__name__)


class HindsightService:
    # Lightweight wrapper around Hindsight's retain/recall/reflect model.
    def __init__(self) -> None:
        self.settings = get_settings()

    def _endpoint_candidates(self, operation: str) -> list[str]:
        base_url = self.settings.hindsight_base_url.rstrip("/")
        candidates = [
            f"{base_url}/{operation}",
            f"{base_url}/api/{operation}",
            f"{base_url}/api/v1/{operation}",
        ]
        seen: set[str] = set()
        unique_candidates: list[str] = []
        for item in candidates:
            if item not in seen:
                unique_candidates.append(item)
                seen.add(item)
        return unique_candidates

    async def retain_memory(
        self,
        user_id: str,
        message: str,
        memory_type: str = "experience_fact",
    ) -> bool:
        # Store meaningful conversation events in per-user bank.
        if not self.settings.hindsight_api_key:
            logger.warning("Hindsight retain skipped: missing API key")
            return False

        async with httpx.AsyncClient(timeout=10) as client:
            for url in self._endpoint_candidates("retain"):
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {self.settings.hindsight_api_key}"},
                    json={"bank_id": user_id, "content": message, "type": memory_type},
                )
                if response.status_code < 400:
                    return True
                if response.status_code != 404:
                    logger.error("Hindsight retain failed (%s): %s", response.status_code, response.text)
                    return False

        logger.error("Hindsight retain failed: no valid endpoint found")
        return False

    async def recall_memory(self, user_id: str, query: str) -> list[str]:
        if not self.settings.hindsight_api_key:
            return []
        async with httpx.AsyncClient(timeout=10) as client:
            for url in self._endpoint_candidates("recall"):
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {self.settings.hindsight_api_key}"},
                    json={"bank_id": user_id, "query": query, "top_k": 8},
                )
                if response.status_code == 404:
                    continue
                if response.status_code >= 400:
                    logger.error("Hindsight recall failed (%s): %s", response.status_code, response.text)
                    return []

                data = response.json()
                return [item.get("content", "") for item in data.get("results", [])]

        logger.error("Hindsight recall failed: no valid endpoint found")
        return []

    async def reflect_on_memory(self, user_id: str, prompt: str) -> dict:
        # Use reflect to synthesize observations from retained facts.
        if not self.settings.hindsight_api_key:
            return {"observations": []}
        async with httpx.AsyncClient(timeout=20) as client:
            for url in self._endpoint_candidates("reflect"):
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {self.settings.hindsight_api_key}"},
                    json={"bank_id": user_id, "query": prompt},
                )
                if response.status_code == 404:
                    continue
                if response.status_code >= 400:
                    logger.error("Hindsight reflect failed (%s): %s", response.status_code, response.text)
                    return {"observations": []}
                return response.json()

        logger.error("Hindsight reflect failed: no valid endpoint found")
        return {"observations": []}


hindsight_service = HindsightService()
