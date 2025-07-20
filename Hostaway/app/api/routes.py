from fastapi import APIRouter, HTTPException, Request
from app.services.pre_check_in_guest_filtering import check_verifications, webhook, arrivals
from app.logging_to_file import setup_logger


logger = setup_logger(__name__)


router = APIRouter()


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


@router.get("/check_arrivals")
def get_verifications():
    logger.info("GET /check_arrivals called")
    try:
        result = arrivals()
        if result['status_code'] == 200:
            return {"status": "success"}

        return {"status": "failed"}
    except Exception as e:
        logger.exception("Error in /check_verifications")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/reservation")
async def webhook_reservation(request: Request):
    logger.info("POST /webhook/reservation called")
    try:
        data = await request.json()
        logger.info(f"Received data: {data}")
        return await webhook(data)
    except Exception as e:
        logger.exception("Error in /webhook/reservation")
        raise HTTPException(status_code=500, detail=str(e))





