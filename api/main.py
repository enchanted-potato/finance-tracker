"""FastAPI application factory — lifespan, CORS middleware, router includes."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import firebase_admin
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials

from app.config import settings
from api.routers import health

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://finance-tracker-rntookejza.web.app",
    "https://finance-tracker-rntookejza.firebaseapp.com",
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown.

    Initialises Firebase Admin SDK on startup (unless dev bypass is active).
    Cleans up on shutdown.

    :param app: The FastAPI application instance.
    """
    firebase_initialised = False

    # Skip Firebase init when dev_user_id is set (local dev / CI / tests)
    if not settings.dev_user_id:
        if settings.firebase_credentials_path:
            cred = credentials.Certificate(settings.firebase_credentials_path)
            firebase_admin.initialize_app(cred)
        else:
            # Application Default Credentials — used on Cloud Run
            firebase_admin.initialize_app()
        firebase_initialised = True

    yield

    if firebase_initialised:
        firebase_admin.delete_app(firebase_admin.get_app())


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(health.router)
