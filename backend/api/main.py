"""FastAPI application for GitExplore."""

from __future__ import annotations

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.logger import configure_logger
from backend.api.routers.health import router as health_router
from backend.api.routers.ingest import router as ingest_router
from backend.api.routers.query import router as query_router


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logger()
    yield


app = FastAPI(
    title="GitExplore API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(ingest_router, prefix="/api/v1")
app.include_router(query_router, prefix="/api/v1")
