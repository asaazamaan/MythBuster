# filepath: d:\Projects\factChecker\api\routes\video_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.video_downloader_service import VideoDownloaderService
from services.transcription_service import TranscriptionService

router = APIRouter()

class VideoProcessRequest(BaseModel):
    urls: List[str]

class VideoProcessResponse(BaseModel):
    success: bool
    message: str
    downloaded_files: List[str]
    transcriptions: List[dict]
    errors: List[str]

@router.post("/process-videos", response_model=VideoProcessResponse)
async def process_videos(request: VideoProcessRequest):
    """Download videos and transcribe them"""
    try:
        # Step 1: Download videos
        downloader = VideoDownloaderService()
        download_result = downloader.download_videos(request.urls)
        
        if not download_result["success"]:
            raise HTTPException(status_code=400, detail=download_result.get("error", "Download failed"))
        
        # Step 2: Transcribe audio files
        transcriber = TranscriptionService()
        transcription_result = transcriber.transcribe_audio_files(download_result["downloaded_files"])
        
        return VideoProcessResponse(
            success=True,
            message=f"Processed {len(request.urls)} URLs successfully",
            downloaded_files=download_result["downloaded_files"],
            transcriptions=transcription_result["transcriptions"],
            errors=download_result["errors"] + transcription_result["errors"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transcriptions")
async def get_transcriptions():
    """Get all existing transcriptions"""
    try:
        transcriber = TranscriptionService()
        result = transcriber.transcribe_audio_files()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))