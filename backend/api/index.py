from app.main import app

# Expose FastAPI application for Vercel Serverless Function runtime
__all__ = ["app"]
