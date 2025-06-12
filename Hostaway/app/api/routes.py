from fastapi import APIRouter, HTTPException, Request
from app.services.reservation import check_registrations, check_verifications, webhook, checkout
from app.logging_to_file import setup_logger


logger = setup_logger(__name__)


router = APIRouter()


@router.get("/check_registrations")
def get_registrations():
    logger.info("GET /check_registrations called")
    try:
        result = check_registrations()
        if result['status_code'] == 200:
            return {"status": "success"}

        return {"status": "failed"}

    except Exception as e:
        logger.exception("Error in /check_registrations")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check_verifications")
def get_verifications():
    logger.info("GET /check_verifications called")
    try:
        result = check_verifications()
        if result['status_code'] == 200:
            return {"status": "success"}

        return {"status": "failed"}
    except Exception as e:
        logger.exception("Error in /check_verifications")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/reservation")
async def webhook_reservation(request: Request):
    logger.info("GET /webhook/reservation called")
    try:
        return await webhook(request)
    except Exception as e:
        logger.exception("Error in /webhook/reservation")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checkout")
def checkout_info():
    logger.info("POST /checkout called")
    try:
        result = checkout()
        if result['status_code'] == 200:
            return {"status": "success"}

        return {"status": "failed"}

    except Exception as e:
        logger.exception("Error in /checkout")
        raise HTTPException(status_code=500, detail=str(e))



