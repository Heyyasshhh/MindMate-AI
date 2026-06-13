from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")
origins = [
    "http://localhost:3000",          # local frontend
    "https://your-app.vercel.app",    # deployed frontend
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix=settings.api_prefix)
