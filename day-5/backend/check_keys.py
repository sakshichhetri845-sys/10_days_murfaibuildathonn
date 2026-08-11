import asyncio
import os

import httpx
from dotenv import load_dotenv

load_dotenv(".env.local")

GEMINI_KEY = os.getenv("GOOGLE_API_KEY", "")
NVIDIA_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")


async def check_gemini():
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            params={"key": GEMINI_KEY},
            json={"contents": [{"parts": [{"text": "hi"}]}]},
        )
        print(f"Gemini status: {r.status_code}")
        if r.status_code != 200:
            msg = r.json().get("error", {}).get("message", r.text)[:300]
            print(f"Gemini error: {msg}")
        else:
            print("Gemini OK")


async def check_nvidia():
    if not NVIDIA_KEY:
        print("NVIDIA status: key missing")
        return

    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {NVIDIA_KEY}"},
            json={
                "model": NVIDIA_MODEL,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
            },
        )
        print(f"NVIDIA status: {r.status_code}")
        if r.status_code != 200:
            msg = r.json().get("error", {}).get("message", "")[:300]
            print(f"NVIDIA error: {msg}")
        else:
            print(f"NVIDIA OK ({NVIDIA_MODEL})")


async def main():
    await check_gemini()
    await check_nvidia()


asyncio.run(main())
