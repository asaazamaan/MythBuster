from fastapi import APIRouter
from fastapi.responses import JSONResponse





@router.get("/health", description="Health check. Returns OK if the service is running")
async def health_check():
    return JSONResponse(content={"status": "OK"}, status_code=200)
