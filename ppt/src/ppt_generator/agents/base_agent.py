"""BaseAgent: Anthropic client wrapper with retry, token counting, and streaming."""
import time
from typing import Any, Type, TypeVar
import anthropic
import instructor
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

MODEL = "claude-sonnet-4-6"
MAX_RETRIES = 3


class BaseAgent:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self._client = anthropic.Anthropic()
        self._instructor = instructor.from_anthropic(self._client)
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def call_structured(
        self,
        user_message: str,
        response_model: Type[T],
        max_tokens: int = 8192,
        temperature: float = 1.0,
        extra_messages: list[dict] | None = None,
    ) -> T:
        messages = extra_messages or []
        messages = messages + [{"role": "user", "content": user_message}]

        for attempt in range(MAX_RETRIES):
            try:
                response, completion = self._instructor.messages.create_with_completion(
                    model=MODEL,
                    max_tokens=max_tokens,
                    system=self.system_prompt,
                    messages=messages,
                    response_model=response_model,
                    temperature=temperature,
                )
                self.total_input_tokens += completion.usage.input_tokens
                self.total_output_tokens += completion.usage.output_tokens
                return response
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                wait = 2 ** attempt
                time.sleep(wait)

    def call_with_thinking(
        self,
        user_message: str,
        response_model: Type[T],
        thinking_budget: int = 4000,
        max_tokens: int = 12000,
    ) -> T:
        """Call Claude with extended thinking enabled (for OutlineAgent)."""
        messages = [{"role": "user", "content": user_message}]

        for attempt in range(MAX_RETRIES):
            try:
                response, completion = self._instructor.messages.create_with_completion(
                    model=MODEL,
                    max_tokens=max_tokens,
                    system=self.system_prompt,
                    messages=messages,
                    response_model=response_model,
                    thinking={"type": "enabled", "budget_tokens": thinking_budget},
                    temperature=1.0,  # required when thinking is enabled
                    betas=["interleaved-thinking-2025-05-14"],
                )
                self.total_input_tokens += completion.usage.input_tokens
                self.total_output_tokens += completion.usage.output_tokens
                return response
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(2 ** attempt)

    def call_raw(
        self,
        user_message: str,
        max_tokens: int = 4096,
        extra_messages: list[dict] | None = None,
    ) -> str:
        """Call Claude and return raw text (no structured output)."""
        messages = extra_messages or []
        messages = messages + [{"role": "user", "content": user_message}]

        response = self._client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=self.system_prompt,
            messages=messages,
        )
        self.total_input_tokens += response.usage.input_tokens
        self.total_output_tokens += response.usage.output_tokens
        return response.content[0].text

    @property
    def token_usage(self) -> dict:
        return {
            "input": self.total_input_tokens,
            "output": self.total_output_tokens,
            "total": self.total_input_tokens + self.total_output_tokens,
        }
