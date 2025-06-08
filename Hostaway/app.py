from fastapi import FastAPI
from api.routes import router as api_router
from script import scheduler


app = FastAPI(
    title="Hostaway Reservation Service",
    description="API to check and list Hostaway reservations",
    version="1.0.0",
)


@app.on_event("startup")
def start_scheduler():
    scheduler.start()


@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()


app.include_router(api_router)