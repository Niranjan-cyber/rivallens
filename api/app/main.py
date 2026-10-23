from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import GIT_SHA, WEB_ORIGIN
from app.modules.profiles.router import router as profiles_router

app = FastAPI(title="RivalLens API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[WEB_ORIGIN],
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(profiles_router)


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True, "version": GIT_SHA}
