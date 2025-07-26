from fastapi import APIRouter
from fastapi.responses import JSONResponse
from .video_routes import router as video_router

router = APIRouter()

@router.get("/health", description="Health check. Returns OK if the service is running")
async def health_check():
    return JSONResponse(content={"status": "OK"}, status_code=200)

# Include video processing routes
router.include_router(video_router, prefix="/videos", tags=["videos"])