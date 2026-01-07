import os
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.config import PORT
from app.api.routes import router as api_router
from app.services.pdf_service import initialize_saxon, release_saxon

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        initialize_saxon()
    except Exception as e:
        print(f"Startup Error: {e}")
    yield
    # Shutdown
    release_saxon()

app = FastAPI(
    title="Peppol XML Visualizer API",
    description="Convert Peppol BIS Billing 3.0 XML to PDF using XSLT and Edge.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router)

if __name__ == "__main__":
    print(f"Starting server on port {PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
