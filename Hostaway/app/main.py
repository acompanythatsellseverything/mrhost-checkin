from fastapi import FastAPI
from app.api.routes import router as api_router

import uvicorn

app = FastAPI(
    title="Hostaway Reservation Service",
    description="API to check and list Hostaway reservations",
    version="1.0.0",
)

app.include_router(api_router)

if __name__ == "__main__":
    print("🚀 Server running at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
