"""
BrokerWeeklyIntel - FastAPI Backend
Main application entrypoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 BrokerWeeklyIntel API starting up...")
    print(f"   Environment: {settings.environment}")
    print(f"   Tracking brokers: {settings.brokers}")
    yield
    # Shutdown
    print("👋 BrokerWeeklyIntel API shutting down...")


app = FastAPI(
    title="BrokerWeeklyIntel API",
    description="Weekly Competitor Intelligence System for Indian Stock Brokers",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "BrokerWeeklyIntel",
        "status": "ok",
        "version": "0.1.0",
        "message": "Weekly Competitor Intelligence API for Zerodha, Groww, Angel One & others",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "environment": settings.environment,
        "brokers_monitored": len(settings.brokers),
    }


# TODO: Include routers from app.api.v1.routers once modules are built
# Example:
# from app.api.v1.routers import reports, brokers, trends
# app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
# app.include_router(brokers.router, prefix="/api/v1/brokers", tags=["Brokers"])
