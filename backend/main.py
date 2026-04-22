"""
Adaptive Training AI — Backend API
Ponto de entrada do servidor FastAPI.

Execucao:
    uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import API_PREFIX, DEBUG
from backend.routers.profiles import router as profiles_router
from backend.routers.state import router as state_router
from backend.routers.microcycle import router as microcycle_router
from backend.routers.sessions import router as sessions_router

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Adaptive Training AI",
    description="Motor de inteligencia para prescricao adaptativa de treinos.",
    version="0.1.0",
    debug=DEBUG,
)

# ---------------------------------------------------------------------------
# CORS — permite o frontend Next.js (localhost:3000) acessar a API
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(profiles_router, prefix=API_PREFIX)
app.include_router(state_router, prefix=API_PREFIX)
app.include_router(microcycle_router, prefix=API_PREFIX)
app.include_router(sessions_router, prefix=API_PREFIX)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint simples para verificar se o servidor esta ativo."""
    return {"status": "ok", "service": "adaptive-training-ai"}
