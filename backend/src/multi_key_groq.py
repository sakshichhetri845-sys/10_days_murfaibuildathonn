"""
Multi-Key Groq LLM Wrapper for LiveKit Agents.

Extends livekit.plugins.groq.LLM with automatic failover across multiple API keys when HTTP 429 / TPM limits occur.
"""

import logging
from typing import Any

import openai
from livekit.agents import DEFAULT_API_CONNECT_OPTIONS, APIConnectOptions, llm
from livekit.agents.llm import ChatContext, ToolChoice
from livekit.agents.llm import utils as llm_utils
from livekit.plugins import groq
from livekit.plugins.openai.llm import NOT_GIVEN, LLMStream, NotGivenOr, is_given
from openai.types.chat import completion_create_params

try:
    from groq_key_manager import groq_key_manager
except ImportError:
    from .groq_key_manager import groq_key_manager

logger = logging.getLogger(__name__)


def _is_rate_limit_error(e: Exception) -> bool:
    """Detect HTTP 429, TPM limit, or rate limit exceeded errors."""
    if isinstance(e, openai.RateLimitError):
        return True
    if getattr(e, "status_code", None) == 429:
        return True
    err_msg = str(e).lower()
    rate_terms = (
        "429",
        "rate_limit_exceeded",
        "too many requests",
        "tpm",
        "tokens per minute",
        "requests per minute",
    )
    return any(term in err_msg for term in rate_terms)


class MultiKeyLLMStream(LLMStream):
    """LLMStream subclass that automatically retries failed generations with next Groq API key on 429 errors."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    async def _run(self) -> None:
        max_attempts = max(1, groq_key_manager.key_count)

        for attempt in range(max_attempts):
            key_index, key_str = groq_key_manager.get_active_key()
            self._client = groq_key_manager.get_client_for_key(key_str)
            logger.info(f"Groq key {key_index} selected")

            try:
                await super()._run()
                logger.info(f"Groq key {key_index} succeeded")
                return
            except Exception as e:
                if _is_rate_limit_error(e):
                    if attempt < max_attempts - 1:
                        groq_key_manager.mark_key_rate_limited(key_index)
                        next_idx, _ = groq_key_manager.get_active_key()
                        logger.warning(
                            f"Groq key {key_index} rate limited, switching to key {next_idx}"
                        )
                        continue
                    else:
                        logger.error("All Groq keys temporarily unavailable")
                        raise e
                else:
                    # Non-rate-limit error (auth, invalid model, syntax) -> re-raise without switching
                    raise e


class MultiKeyGroqLLM(groq.LLM):
    """Groq LLM implementation with multi-key failover support."""

    def __init__(
        self,
        *,
        model: str = "llama-3.1-8b-instant",
        **kwargs: Any,
    ) -> None:
        # Get current active key from GroqKeyManager
        if groq_key_manager.key_count > 0:
            _key_idx, active_key = groq_key_manager.get_active_key()
            client = groq_key_manager.get_client_for_key(active_key)
            kwargs["api_key"] = active_key
            kwargs["client"] = client
        super().__init__(model=model, **kwargs)

    def chat(
        self,
        *,
        chat_ctx: ChatContext,
        tools: list[llm.Tool] | None = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        parallel_tool_calls: NotGivenOr[bool] = NOT_GIVEN,
        tool_choice: NotGivenOr[ToolChoice] = NOT_GIVEN,
        response_format: NotGivenOr[
            completion_create_params.ResponseFormat | type[llm_utils.ResponseFormatT]
        ] = NOT_GIVEN,
        extra_kwargs: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
    ) -> LLMStream:
        # Prepare parameters identically to OpenAILLM.chat
        extra = {}
        if is_given(extra_kwargs):
            extra.update(extra_kwargs)

        if is_given(self._opts.extra_body):
            extra["extra_body"] = self._opts.extra_body

        if is_given(self._opts.extra_headers):
            extra["extra_headers"] = self._opts.extra_headers

        if is_given(self._opts.extra_query):
            extra["extra_query"] = self._opts.extra_query

        if is_given(self._opts.metadata):
            extra["metadata"] = self._opts.metadata

        if is_given(self._opts.user):
            extra["user"] = self._opts.user

        if is_given(self._opts.max_completion_tokens):
            extra["max_completion_tokens"] = self._opts.max_completion_tokens

        if is_given(self._opts.temperature):
            extra["temperature"] = self._opts.temperature

        if is_given(self._opts.service_tier):
            extra["service_tier"] = self._opts.service_tier

        if is_given(self._opts.reasoning_effort):
            extra["reasoning_effort"] = self._opts.reasoning_effort

        if is_given(self._opts.safety_identifier):
            extra["safety_identifier"] = self._opts.safety_identifier

        if is_given(self._opts.prompt_cache_key):
            extra["prompt_cache_key"] = self._opts.prompt_cache_key

        if is_given(self._opts.top_p):
            extra["top_p"] = self._opts.top_p

        p_tool_calls = (
            parallel_tool_calls
            if is_given(parallel_tool_calls)
            else self._opts.parallel_tool_calls
        )
        if is_given(p_tool_calls):
            extra["parallel_tool_calls"] = p_tool_calls

        t_choice = tool_choice if is_given(tool_choice) else self._opts.tool_choice
        if is_given(t_choice):
            if isinstance(t_choice, dict):
                extra["tool_choice"] = {
                    "type": "function",
                    "function": {"name": t_choice["function"]["name"]},
                }
            elif t_choice in ("auto", "required", "none"):
                extra["tool_choice"] = t_choice

        if is_given(response_format):
            extra["response_format"] = llm_utils.to_openai_response_format(
                response_format
            )

        _key_idx, active_key = groq_key_manager.get_active_key()
        active_client = groq_key_manager.get_client_for_key(active_key)

        return MultiKeyLLMStream(
            self,
            model=self._opts.model,
            provider_fmt=self._provider_fmt,
            strict_tool_schema=self._strict_tool_schema,
            client=active_client,
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options,
            extra_kwargs=extra,
        )
