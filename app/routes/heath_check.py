from fastapi import APIRouter

router = APIRouter(
    prefix="/server",
    tags=["server status check"]  # for swagger
)


@router.get("/health-check")
async def check_health():
    return {"status": "online"}
