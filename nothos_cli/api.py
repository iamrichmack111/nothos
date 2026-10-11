"""Local REST API for NOTHOS research."""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .engine import run_research

app = FastAPI(
    title="NOTHOS Research API",
    description="Ancient Greek philology, mythology and evidence-aware research.",
    version="6.0.0",
)


class ResearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=8, ge=1, le=100)
    ai: bool = True
    engine: str = "lsj"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "nothos",
        "version": "6.0.0",
    }


@app.get("/api/v1/search")
def search(
    q: str = Query(min_length=1, max_length=2000),
    top_k: int = Query(default=8, ge=1, le=100),
):
    try:
        return run_research(q, top_k=top_k, ai=False)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/v1/research")
def research(request: ResearchRequest):
    try:
        return run_research(
            request.query,
            top_k=request.top_k,
            ai=request.ai,
            engine=request.engine,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
