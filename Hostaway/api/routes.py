from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request, FastAPI
from services.reservation import check_registrations, check_verifications, webhook
from logging_to_file import setup_logger


logger = setup_logger(__name__)
load_dotenv()


router = APIRouter()


@router.get("/check_registrations")
def get_registrations():
    logger.info("GET /check_registrations called")
    try:
        result = check_registrations()
        logger.info(f"Found {len(result)} registration results")
        return result

    except Exception as e:
        logger.exception("Error in /check_registrations")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check_verifications")
def get_verifications():
    logger.info("GET /check_verifications called")
    try:
        result = check_verifications()
        logger.info(f"Found {len(result)} verification results")
        return result
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



