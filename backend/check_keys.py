import os
import httpx
import asyncio

GEMINI_KEY = os.getenv("GOOGLE_API_KEY", "")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")

async def check_gemini():
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            params={"key": GEMINI_KEY},
            json={"contents": [{"parts": [{"text": "hi"}]}]}
        )
        print(f"Gemini status: {r.status_code}")
        if r.status_code != 200:
            msg = r.json().get("error", {}).get("message", r.text)[:300]
            print(f"Gemini error: {msg}")
        else:
            print("Gemini OK")

async def check_groq():
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1}
        )
        print(f"Groq status: {r.status_code}")
        remaining = r.headers.get("x-ratelimit-remaining-tokens-day", "unknown")
        print(f"Groq tokens remaining today: {remaining}")
        if r.status_code != 200:
            msg = r.json().get("error", {}).get("message", "")[:300]
            print(f"Groq error: {msg}")
        else:
            print("Groq OK")

async def main():
    await check_gemini()
    await check_groq()

asyncio.run(main())
