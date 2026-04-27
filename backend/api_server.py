from __future__ import annotations

import backend.config  # ensures load_dotenv runs early!
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.microcycle_router import router as microcycle_router
from backend.routers.rag_router import router as rag_router

app = FastAPI(title="Adaptive Training API", version="0.1.0")

# Permissive localhost CORS: Next.js dev server runs on :3000 and may also
# be tunneled via 127.0.0.1; tighten this in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rag_router, prefix="/api/rag")
app.include_router(microcycle_router, prefix="/api/microcycle")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
