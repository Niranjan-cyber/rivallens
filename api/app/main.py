import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import jobs
from app.config import GIT_SHA, WEB_ORIGIN
from app.modules.alerts.router import router as alerts_router
from app.modules.changes.router import router as changes_router
from app.modules.demo.router import router as demo_router
from app.modules.discovery.router import router as discovery_router
from app.modules.profiles.router import router as profiles_router

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")  # app logs (llm cache hits, job failures) reach Render


@asynccontextmanager
async def lifespan(_: FastAPI):
    jobs.mark_stale()
    yield


app = FastAPI(title="RivalLens API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[WEB_ORIGIN],
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(profiles_router)
app.include_router(demo_router)
app.include_router(changes_router)
app.include_router(alerts_router)
app.include_router(discovery_router)


@app.exception_handler(HTTPException)
def error_shape(_: Request, exc: HTTPException) -> JSONResponse:
    # Specs §2 error shape: {"error": {"code", "message"}}
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "http_error", "message": str(exc.detail)}
    return JSONResponse({"error": detail}, status_code=exc.status_code, headers=exc.headers)


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True, "version": GIT_SHA}
