from __future__ import annotations

from pathlib import Path
from app.core.config import get_settings


SYSTEM_PROMPT = Path(__file__).parent / "prompts" / "system_prompt.txt"


class CareerMentorAgent:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.instructions = SYSTEM_PROMPT.read_text(encoding="utf-8")

    async def respond(self, user_id: str, message: str, memory_context: list[str], observations: list[str]) -> str:
        # Agno-first path with graceful fallback if dependency/model config is unavailable.
        try:
            from agno.agent import Agent
            from agno.models.openai import OpenAIChat

            model = OpenAIChat(id=self.settings.openai_model, api_key=self.settings.openai_api_key)
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
        except Exception:
            memory_line = memory_context[0] if memory_context else "No prior memory yet."
            observation_line = observations[0] if observations else "No behavior observation yet."
            return (
                f"Career guidance: based on your history, {observation_line}. "
                f"Relevant context: {memory_line}. "
                "Next steps: (1) apply to 3 relevant roles today, (2) improve one project bullet with quantified impact, "
                "(3) practice one interview topic for 30 minutes."
            )


career_mentor_agent = CareerMentorAgent()
