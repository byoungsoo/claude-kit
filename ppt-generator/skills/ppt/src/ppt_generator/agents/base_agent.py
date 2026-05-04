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
        """Call Claude with extended thinking enabled (for OutlineAgent).

        Bypasses instructor because betas/thinking params aren't forwarded
        through instructor's create_with_completion. Instead, we append an
        explicit JSON extraction prompt and parse the output directly.
        """
        import json

        schema_str = json.dumps(response_model.model_json_schema(), ensure_ascii=False, indent=2)
        full_message = (
            f"{user_message}\n\n"
            f"다음 JSON 스키마에 맞게 응답하세요. JSON 외에 다른 텍스트는 포함하지 마세요:\n"
            f"```json\n{schema_str}\n```"
        )
        messages = [{"role": "user", "content": full_message}]

        for attempt in range(MAX_RETRIES):
            try:
                completion = self._client.beta.messages.create(
                    model=MODEL,
                    max_tokens=max_tokens,
                    system=self.system_prompt,
                    messages=messages,
                    thinking={"type": "enabled", "budget_tokens": thinking_budget},
                    temperature=1.0,
                    betas=["interleaved-thinking-2025-05-14"],
                )
                self.total_input_tokens += completion.usage.input_tokens
                self.total_output_tokens += completion.usage.output_tokens

                # Extract text from content blocks (skip thinking blocks)
                raw_text = ""
                for block in completion.content:
                    if block.type == "text":
                        raw_text = block.text
                        break

                # Strip markdown code fences if present
                raw_text = raw_text.strip()
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("```", 2)[1]
                    if raw_text.startswith("json"):
                        raw_text = raw_text[4:]
                    raw_text = raw_text.rsplit("```", 1)[0].strip()

                data = json.loads(raw_text)
                return response_model.model_validate(data)
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
