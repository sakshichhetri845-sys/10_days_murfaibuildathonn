import asyncio
import os

import httpx
from dotenv import load_dotenv

load_dotenv(".env.local")


async def test_groq():
    key = (
        os.getenv("GROQ_API_KEY", "").strip() or os.getenv("GROQ_API_KEY_1", "").strip()
    )
    print(f"Groq key (first 10 chars): {key[:10]}...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": "say hello"}],
                "max_tokens": 10,
            },
        )
        print(f"Groq status: {resp.status_code}")
        print(f"Groq body: {resp.text[:300]}")


async def test_deepgram():
    key = os.getenv("DEEPGRAM_API_KEY", "").strip()
    print(f"\nDeepgram key (first 10 chars): {key[:10]}...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://api.deepgram.com/v1/projects",
            headers={"Authorization": f"Token {key}"},
        )
        print(f"Deepgram status: {resp.status_code}")


async def test_murf():
    key = os.getenv("MURF_API_KEY", "").strip()
    print(f"\nMurf key (first 10 chars): {key[:10]}...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://api.murf.ai/v1/speech/voices",
            headers={"api-key": key},
        )
        print(f"Murf status: {resp.status_code}")


asyncio.run(test_groq())
asyncio.run(test_deepgram())
asyncio.run(test_murf())
