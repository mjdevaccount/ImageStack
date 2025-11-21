from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import health, vision, ocr, debug_preprocess
from .utils.logging_config import configure_logging

configure_logging()

app = FastAPI(
    title="ImageStack",
    description="Local multimodal/vision server",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(vision.router, prefix="/vision", tags=["vision"])
app.include_router(ocr.router, prefix="/ocr", tags=["ocr"])
app.include_router(debug_preprocess.router, prefix="/debug", tags=["debug"])

