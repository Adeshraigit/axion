from __future__ import annotations

import logging
import httpx
from app.core.config import get_settings


logger = logging.getLogger(__name__)


class HindsightService:
    # Lightweight wrapper around Hindsight's retain/recall/reflect model.
    def __init__(self) -> None:
        self.settings = get_settings()

    def _base_url_candidates(self) -> list[str]:
        base_url = (self.settings.hindsight_base_url or "").strip().rstrip("/")
        return [base_url] if base_url else []

    def _operation_aliases(self, operation: str) -> list[str]:
        aliases = {
            "retain": ["retain", "store", "ingest"],
            "recall": ["recall", "retrieve", "search", "query"],
            "reflect": ["reflect", "insights"],
        }
        return aliases.get(operation, [operation])

    def _endpoint_candidates(self, operation: str) -> list[str]:
        candidates: list[str] = []
        base_urls = self._base_url_candidates()
        operations = self._operation_aliases(operation)

        for base_url in base_urls:
            for op in operations:
                candidates.extend(
                    [
                        f"{base_url}/{op}",
                        f"{base_url}/v1/{op}",
                        f"{base_url}/memory/{op}",
                        f"{base_url}/memories/{op}",
                        f"{base_url}/api/{op}",
                        f"{base_url}/api/v1/{op}",
                        f"{base_url}/v1/memory/{op}",
                        f"{base_url}/v1/memories/{op}",
                        f"{base_url}/api/v1/memory/{op}",
                        f"{base_url}/api/v1/memories/{op}",
                    ]
                )

        seen: set[str] = set()
        unique_candidates: list[str] = []
        for item in candidates:
            if item not in seen:
                unique_candidates.append(item)
                seen.add(item)
        return unique_candidates

    async def _post_with_candidates(
        self,
        client: httpx.AsyncClient,
        operation: str,
        payload: dict,
    ) -> httpx.Response | None:
        transport_failures = 0
        last_transport_error: str | None = None

        for url in self._endpoint_candidates(operation):
            try:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {self.settings.hindsight_api_key}"},
                    json=payload,
                )
            except httpx.HTTPError as exc:
                transport_failures += 1
                last_transport_error = str(exc)
                continue

            if response.status_code == 404:
                continue
            return response

        if transport_failures > 0:
            logger.error(
                "Hindsight %s failed: %s transport errors while probing configured base URL %s. Last error: %s",
                operation,
                transport_failures,
                self.settings.hindsight_base_url,
                last_transport_error or "unknown",
            )

        return None

    def _bank_id(self, user_id: str) -> str:
        configured = (self.settings.hindsight_bank_id or "").strip()
        return configured or user_id

    def _extract_text_candidates(self, node: object) -> list[str]:
        if isinstance(node, str):
            text = node.strip()
            return [text] if text else []

        if isinstance(node, list):
            results: list[str] = []
            for item in node:
                results.extend(self._extract_text_candidates(item))
            return results

        if isinstance(node, dict):
            # Prefer known memory text fields first.
            ordered_keys = [
                "content",
                "memory",
                "text",
                "value",
                "summary",
                "fact",
                "observation",
                "description",
            ]
            results: list[str] = []
            for key in ordered_keys:
                if key in node:
                    results.extend(self._extract_text_candidates(node[key]))

            # Traverse nested containers commonly used by providers.
            for key, value in node.items():
                if key in {
                    "results",
                    "memories",
                    "items",
                    "matches",
                    "world_facts",
                    "facts",
                    "data",
                    "nodes",
                    "observations",
                }:
                    results.extend(self._extract_text_candidates(value))

            return results

        return []

    def _extract_unique_memories(self, payload: object) -> list[str]:
        memories = self._extract_text_candidates(payload)
        unique: list[str] = []
        seen: set[str] = set()
        for memory in memories:
            cleaned = " ".join(memory.split())
            if not cleaned:
                continue
            if cleaned in seen:
                continue
            seen.add(cleaned)
            unique.append(cleaned)
        return unique

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
        if not self.settings.hindsight_base_url:
            logger.warning("Hindsight retain skipped: missing base URL")
            return False

        async with httpx.AsyncClient(timeout=10) as client:
            bank_id = self._bank_id(user_id)
            response = await self._post_with_candidates(
                client,
                "retain",
                {"bank_id": bank_id, "content": message, "type": memory_type},
            )
            if response is None:
                logger.error("Hindsight retain failed: no valid endpoint found")
                return False

            if response.status_code >= 400:
                logger.error("Hindsight retain failed (%s): %s", response.status_code, response.text)
                return False

            return True

    async def recall_memory(self, user_id: str, query: str) -> list[str]:
        if not self.settings.hindsight_api_key:
            return []
        if not self.settings.hindsight_base_url:
            return []

        async with httpx.AsyncClient(timeout=10) as client:
            bank_id = self._bank_id(user_id)
            response = await self._post_with_candidates(
                client,
                "recall",
                {"bank_id": bank_id, "query": query, "top_k": 8},
            )
            if response is None:
                logger.error("Hindsight recall failed: no valid endpoint found")
                return []

            if response.status_code >= 400:
                logger.error("Hindsight recall failed (%s): %s", response.status_code, response.text)
                return []

            try:
                data = response.json()
            except ValueError:
                logger.error("Hindsight recall returned invalid JSON")
                return []

            memories = self._extract_unique_memories(data)
            if memories:
                return memories[:8]

            logger.warning("Hindsight recall succeeded but returned no parseable memories")
            return []

    async def reflect_on_memory(self, user_id: str, prompt: str) -> dict:
        # Use reflect to synthesize observations from retained facts.
        if not self.settings.hindsight_api_key:
            return {"observations": []}
        if not self.settings.hindsight_base_url:
            return {"observations": []}

        async with httpx.AsyncClient(timeout=20) as client:
            bank_id = self._bank_id(user_id)
            response = await self._post_with_candidates(
                client,
                "reflect",
                {"bank_id": bank_id, "query": prompt},
            )
            if response is None:
                logger.error("Hindsight reflect failed: no valid endpoint found")
                return {"observations": []}

            if response.status_code >= 400:
                logger.error("Hindsight reflect failed (%s): %s", response.status_code, response.text)
                return {"observations": []}
            try:
                return response.json()
            except ValueError:
                logger.error("Hindsight reflect returned invalid JSON")
                return {"observations": []}


hindsight_service = HindsightService()
