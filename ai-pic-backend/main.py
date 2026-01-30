"""Uvicorn entrypoint.

The Docker dev stack starts the backend via `uvicorn main:app`, so this module
must expose a top-level `app` object.
"""

import uvicorn
from app.main import app  # noqa: F401

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
