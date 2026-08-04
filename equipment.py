import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.database import Base, engine
from backend.app.routers import (
    calculate,
    datasheets,
    equipment,
    health,
    projects,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AIngeFV API",
    version="1.0.3",
)

origins = [
    item.strip()
    for item in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if item.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    health.router,
    prefix="/api/health",
    tags=["health"],
)
app.include_router(
    calculate.router,
    prefix="/api/calculate",
    tags=["calculation"],
)
app.include_router(
    datasheets.router,
    prefix="/api/datasheet",
    tags=["datasheets"],
)
app.include_router(
    equipment.router,
    prefix="/api/equipment",
    tags=["equipment"],
)
app.include_router(
    projects.router,
    prefix="/api/projects",
    tags=["projects"],
)
