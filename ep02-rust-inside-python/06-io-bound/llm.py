"""A stand-in for a real LLM API client.

It just waits, like a network call to a model would. Swap in your real client
(OpenAI, Anthropic, a vLLM server...) and the flame graph looks the same:
most of the time is spent waiting, and no Rust rewrite changes that.
"""
import asyncio
import os

LATENCY_S = float(os.getenv("FAKE_LLM_LATENCY", "1.5"))


async def complete(prompt: str) -> str:
    await asyncio.sleep(LATENCY_S)
    return f"(summary of {len(prompt)} characters)"
