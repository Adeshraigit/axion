from __future__ import annotations

from pathlib import Path
import logging
from app.core.config import get_settings


SYSTEM_PROMPT = Path(__file__).parent / "prompts" / "system_prompt.txt"
logger = logging.getLogger(__name__)


class CareerMentorAgent:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.instructions = SYSTEM_PROMPT.read_text(encoding="utf-8")

    async def respond(self, user_id: str, message: str, memory_context: list[str], observations: list[str]) -> str:
        # Agno-first path with graceful fallback if dependency/model config is unavailable.
        try:
            from agno.agent import Agent
            from agno.models.openai import OpenAIChat

            api_key = self.settings.openai_api_key.strip()
            base_url = self.settings.openai_base_url.strip() or None

            if not api_key:
                raise ValueError("OPENAI_API_KEY is missing")

            if api_key.startswith("gsk_") and not base_url:
                base_url = "https://api.groq.com/openai/v1"
                logger.info("Detected Groq key prefix; using default OPENAI_BASE_URL=%s", base_url)

            model = OpenAIChat(
                id=self.settings.openai_model,
                api_key=api_key,
                base_url=base_url,
            )
            agent = Agent(model=model, instructions=self.instructions)
            prompt = (
                f"User ID: {user_id}\n"
                f"Recalled memory: {memory_context}\n"
                f"Observations: {observations}\n"
                f"User message: {message}\n"
                "Return concise mentorship with skill gaps and next actions."
            )
            run_output = agent.run(prompt)
            return str(getattr(run_output, "content", run_output))
        except Exception as exc:
            logger.warning("CareerMentorAgent fallback activated: %s", exc)
            memory_line = memory_context[0] if memory_context else "No prior memory yet."
            observation_line = observations[0] if observations else "No behavior observation yet."
            return (
                f"Career guidance: based on your history, {observation_line}. "
                f"Relevant context: {memory_line}. "
                "Next steps: (1) apply to 3 relevant roles today, (2) improve one project bullet with quantified impact, "
                "(3) practice one interview topic for 30 minutes."
            )


career_mentor_agent = CareerMentorAgent()
