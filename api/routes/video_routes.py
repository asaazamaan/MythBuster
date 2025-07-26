import os
import requests
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import datetime

from services.video_downloader_service import VideoDownloaderService
from services.transcription_service import TranscriptionService
from models.video import Video
from databases import get_session


def get_db():
    session_gen = get_session()
    return next(session_gen)  # Extract Session from generator


router = APIRouter()


# ✅ Updated request/response models
class VideoProcessRequest(BaseModel):
    url: str


class VideoProcessResponse(BaseModel):
    success: bool
    message: str
    videoID: Optional[int]
    url: str
    title: Optional[str]
    transcription: Optional[str]
    claims: List[str]
    verdicts: List[dict]  # ✅ Added verdicts field
    processed_at: Optional[datetime.datetime]
    from_cache: bool  # Indicates if result came from database


def extract_claims_from_transcript(transcript_text):
    """Extract diabetes claims and fact-check them using Gemini - Returns claims and verdicts"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️ Warning: GEMINI_API_KEY not found, skipping claim extraction")
            return [], []

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

        prompt = f"""
You are an expert medical fact-checker for an "AI MythBuster" project. Your task is to analyze the provided video transcript to identify and extract factual claims AND fact-check them using medical knowledge.

You must follow these rules strictly:
1. The transcript may contain spelling errors, grammar mistakes, and conversational fillers. Ignore these errors and focus on understanding the intended meaning of the text.
2. Read the transcript carefully to determine if the primary topic and claims are related to the medical field of "Diabetes" or diabetic care.
3. If the transcript's claims are NOT about Diabetes, your output MUST be this exact JSON object:
   {{"domain_is_diabetes": false, "claims_with_verdicts": []}}

4. If the transcript's claims ARE about Diabetes, identify the main claims.
   - Prioritize extracting any claims that are likely to be medically misleading, exaggerated, or incorrect. If no such claims are found, then extract up to three significant factual claims. All claims must be written in correct Arabic, clearly and objectively, while preserving the speaker’s original intended meaning without softening or interpreting it.
   - Focus on the single most significant claim if possible.
   - If a single main claim cannot be identified, extract up to a maximum of three distinct, verifiable claims.
   - Each claim should be a concise, objective statement written in Arabic language.
   - For EACH claim, provide a medical fact-check verdict using your medical knowledge to assess accuracy.

5. For each claim, determine the verdict:
   - TRUE: Medically accurate based on established diabetes knowledge
   - FALSE: Medically incorrect or contradicts established knowledge  
   - PARTIALLY_TRUE: Contains some truth but incomplete/misleading
   - INSUFFICIENT_INFO: Cannot determine accuracy with available medical knowledge

6. Your output MUST be this exact JSON format, with the boolean value and claims_with_verdicts array filled in based on the rules above. All claims must be written in Arabic. Do not include any other text, explanations, or conversational language.

{{
  "domain_is_diabetes": true,
  "claims_with_verdicts": [
    {{
      "claim": "Arabic claim text",
      "verdict": "TRUE|FALSE|PARTIALLY_TRUE|INSUFFICIENT_INFO",
      "confidence": 0.85,
      "reasoning": "Brief medical explanation in Arabic",
      "medical_category": "treatment|prevention|symptoms|causes|diet|lifestyle"
    }}
  ]
}}

Transcript to analyze:
"{transcript_text}"
"""

        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        headers = {"Content-Type": "application/json"}

        response = requests.post(url, json=payload, headers=headers, timeout=60)

        if response.status_code == 200:
            response_data = response.json()
            candidates = response_data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    extracted_text = parts[0].get("text", "").strip()

                    try:
                        if extracted_text.startswith("```json"):
                            extracted_text = (
                                extracted_text.replace("```json", "")
                                .replace("```", "")
                                .strip()
                            )

                        parsed_response = json.loads(extracted_text)

                        if parsed_response.get("domain_is_diabetes", False):
                            claims_with_verdicts = parsed_response.get("claims_with_verdicts", [])
                            claims = [item["claim"] for item in claims_with_verdicts]
                            verdicts = claims_with_verdicts
                            print(f"✅ Diabetes video detected. Claims: {len(claims)}, Verdicts: {len(verdicts)}")
                            return claims, verdicts
                        else:
                            print("ℹ️ Video is not about diabetes, skipping claim extraction")
                            return [], []

                    except json.JSONDecodeError:
                        print(f"❌ Failed to parse JSON response: {extracted_text}")
                        # Fallback: extract claims without verdicts
                        claims = [
                            claim.strip()
                            for claim in extracted_text.split("\n")
                            if claim.strip()
                        ]
                        return claims[:3], []

            return [], []
        else:
            print(f"❌ Gemini API error: {response.status_code} - {response.text}")
            return [], []

    except Exception as e:
        print(f"❌ Error extracting claims: {str(e)}")
        return [], []


# ✅ Main endpoint with database caching
@router.post("/process-video", response_model=VideoProcessResponse)
async def process_video(request: VideoProcessRequest, db: Session = Depends(get_db)):
    """Process video with database caching and fact-checking"""
    try:
        print(f"🚀 Processing video: {request.url}")

        # ✅ Step 1: Check if URL exists in database
        existing_video = db.query(Video).filter(Video.url == request.url).first()

        if existing_video:
            print(f"⚡ Found cached result for: {request.url}")
            return VideoProcessResponse(
                success=True,
                message="Retrieved from cache",
                videoID=existing_video.videoID,
                url=existing_video.url,
                title=existing_video.title,
                transcription=existing_video.transcription,
                claims=existing_video.claims,
                verdicts=existing_video.verdicts if hasattr(existing_video, 'verdicts') else [],
                processed_at=existing_video.processed_at,
                from_cache=True,
            )

        # ✅ Step 2: Process new video
        print(f"🔄 Processing new video: {request.url}")

        # Download video
        downloader = VideoDownloaderService()
        download_result = downloader.download_videos([request.url])
        print(f"📥 Download result: {download_result}")

        if not download_result["success"] or not download_result["downloaded_files"]:
            raise HTTPException(status_code=400, detail="Failed to download video")

        downloaded_file = download_result["downloaded_files"][0]
        print(f"📁 File to transcribe: {downloaded_file}")

        # Get video title from filename (remove .mp3 extension)
        video_title = (
            downloaded_file.replace(".mp3", "")
            if downloaded_file.endswith(".mp3")
            else downloaded_file
        )

        # Transcribe video
        print(f"🎤 Starting transcription...")
        transcriber = TranscriptionService()
        transcription_result = transcriber.transcribe_audio_files([downloaded_file])
        print(f"🎤 Transcription result: {transcription_result}")

        if not transcription_result["transcriptions"]:
            raise HTTPException(status_code=500, detail="Failed to transcribe video")

        transcription = transcription_result["transcriptions"][0]
        print(f"🎤 Transcribed: {transcription['filename']}")

        # Extract claims and fact-check them
        claims = []
        verdicts = []
        if transcription["success"]:
            print(f"🔍 Extracting and fact-checking claims from: {transcription['filename']}")
            claims, verdicts = extract_claims_from_transcript(transcription["transcription"])

        print(f"✅ Extracted {len(claims)} claims with {len(verdicts)} fact-checks")

        # ✅ Step 3: Save to database
        new_video = Video(
            url=request.url,
            title=video_title,
            transcription=(
                transcription["transcription"] if transcription["success"] else None
            ),
            claims=claims,
            verdicts=verdicts,  # ✅ Save verdicts to database
        )

        db.add(new_video)
        db.commit()
        db.refresh(new_video)

        print(f"💾 Saved to database with ID: {new_video.videoID}")

        return VideoProcessResponse(
            success=True,
            message="Successfully processed and fact-checked video",
            videoID=new_video.videoID,
            url=new_video.url,
            title=new_video.title,
            transcription=new_video.transcription,
            claims=new_video.claims,
            verdicts=new_video.verdicts,  # ✅ Return verdicts
            processed_at=new_video.processed_at,
            from_cache=False,
        )

    except Exception as e:
        print(f"❌ FULL ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ✅ Cleanup endpoint
@router.delete("/clean-downloads")
async def clean_downloads():
    """Clean up all downloaded files"""
    try:
        transcriber = TranscriptionService()
        result = transcriber.cleanup_audio_files()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ Enhanced endpoint: Get cached videos with verdicts
@router.get("/cached-videos")
async def get_cached_videos(db: Session = Depends(get_db)):
    """Get list of all cached videos with fact-check results"""
    try:
        videos = db.query(Video).order_by(Video.processed_at.desc()).all()
        return {
            "success": True,
            "total_videos": len(videos),
            "videos": [
                {
                    "videoID": v.videoID,
                    "url": v.url,
                    "title": v.title,
                    "claims_count": len(v.claims),
                    "verdicts_count": len(v.verdicts) if hasattr(v, 'verdicts') else 0,
                    "processed_at": v.processed_at,
                }
                for v in videos
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))