from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routes import catalog, health, locations, profiles, rankings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    get_settings().raw_storage_path.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Norevia API",
    version="0.1.0",
    lifespan=lifespan,
    description="Transparent destination comparison API with explicit provenance and data quality.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Accept-Language", "X-User-Id"],
)
app.include_router(health.router)
for router in (locations.router, catalog.router, rankings.router, profiles.router):
    app.include_router(router, prefix="/api/v1")


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "messageKey": "errors.validation",
                "context": {"fields": exc.errors()},
            },
        },
    )
