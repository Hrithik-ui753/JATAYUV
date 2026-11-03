import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import asyncio
import httpx
from backend.app.main import app

async def main():
    print("Initializing httpx.AsyncClient with ASGITransport...")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/health")
        print("Health status:", r.status_code, r.json())
        assert r.status_code == 200
        print("Success! FastAPI ASGI Transport works instantaneously.")

if __name__ == "__main__":
    asyncio.run(main())
