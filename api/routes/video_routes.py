# # filepath: d:\Projects\factChecker\api\routes\video_routes.py
# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from typing import List
# from services.video_downloader_service import VideoDownloaderService
# from services.transcription_service import TranscriptionService

# router = APIRouter()

# class VideoProcessRequest(BaseModel):
#     urls: List[str]

# class VideoProcessResponse(BaseModel):
#     success: bool
#     message: str
#     downloaded_files: List[str]
#     transcriptions: List[dict]
#     errors: List[str]

# @router.post("/process-videos", response_model=VideoProcessResponse)
# async def process_videos(request: VideoProcessRequest):
#     """Download videos and transcribe them"""
#     try:
#         # Step 1: Download videos
#         downloader = VideoDownloaderService()
#         download_result = downloader.download_videos(request.urls)
        
#         if not download_result["success"]:
#             raise HTTPException(status_code=400, detail=download_result.get("error", "Download failed"))
        
#         # Step 2: Transcribe audio files
#         transcriber = TranscriptionService()
#         transcription_result = transcriber.transcribe_audio_files(download_result["downloaded_files"])
        
#         return VideoProcessResponse(
#             success=True,
#             message=f"Processed {len(request.urls)} URLs successfully",
#             downloaded_files=download_result["downloaded_files"],
#             transcriptions=transcription_result["transcriptions"],
#             errors=download_result["errors"] + transcription_result["errors"]
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/transcriptions")
# async def get_transcriptions():
#     """Get all existing transcriptions"""
#     try:
#         transcriber = TranscriptionService()
#         result = transcriber.transcribe_audio_files()
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

import os
import requests
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
    claims: List[str]
    errors: List[str]

def extract_claims_from_transcript(transcript_text):
    """Extract diabetes claims using specialized Gemini prompt"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️ Warning: GEMINI_API_KEY not found, skipping claim extraction")
            return []
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        prompt = f"""
You are an expert medical fact-checker for an "AI MythBuster" project. Your task is to analyze the provided video transcript to identify and extract factual claims.

You must follow these rules strictly:
1.  The transcript may contain spelling errors, grammar mistakes, and conversational fillers. Ignore these errors and focus on understanding the intended meaning of the text.
2.  Read the transcript carefully to determine if the primary topic and claims are related to the medical field of "Diabetes" or diabetic care.
3.  If the transcript's claims are NOT about Diabetes, your output MUST be this exact JSON object:
    {{"domain_is_diabetes": false, "claims": []}}
4.  If the transcript's claims ARE about Diabetes, identify the main claims.
    - Focus on the single most significant claim if possible.
    - If a single main claim cannot be identified, extract up to a maximum of three distinct, verifiable claims.
    - Each claim should be a concise, objective statement.

5.  Your output MUST be this exact JSON format, with the boolean value and claims array filled in based on the rules above. Do not include any other text, explanations, or conversational language.

Transcript to analyze:
"{transcript_text}"
        """
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            candidates = response_data.get('candidates', [])
            if candidates:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if parts:
                    extracted_text = parts[0].get('text', '').strip()
                    
                    # ✅ Parse JSON response from Gemini
                    try:
                        import json
                        # Remove any markdown formatting if present
                        if extracted_text.startswith('```json'):
                            extracted_text = extracted_text.replace('```json', '').replace('```', '').strip()
                        
                        # Parse the JSON response
                        parsed_response = json.loads(extracted_text)
                        
                        # Check if it's diabetes-related
                        if parsed_response.get("domain_is_diabetes", False):
                            return parsed_response.get("claims", [])
                        else:
                            print("ℹ️ Video is not about diabetes, skipping claim extraction")
                            return []
                            
                    except json.JSONDecodeError:
                        print(f"❌ Failed to parse JSON response: {extracted_text}")
                        # Fallback to simple text parsing
                        claims = [claim.strip() for claim in extracted_text.split('\n') if claim.strip()]
                        return claims[:3]  # Limit to 3 claims
            
            return []
        else:
            print(f"❌ Gemini API error: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Error extracting claims: {str(e)}")
        return []

@router.post("/process-videos", response_model=VideoProcessResponse)
async def process_videos(request: VideoProcessRequest):
    """Download videos, transcribe them, and extract claims"""
    try:
        # Step 1: Download videos
        downloader = VideoDownloaderService()
        download_result = downloader.download_videos(request.urls)
        
        if not download_result["success"]:
            raise HTTPException(status_code=400, detail=download_result.get("error", "Download failed"))
        
        # Step 2: Transcribe audio files
        transcriber = TranscriptionService()
        transcription_result = transcriber.transcribe_audio_files(download_result["downloaded_files"])

        # Step 3: Extract claims from transcriptions
        all_claims = []
        for transcription in transcription_result["transcriptions"]:
            if transcription["success"]:
                claims = extract_claims_from_transcript(transcription["transcription"])
                all_claims.extend(claims)

        return VideoProcessResponse(
            success=True,
            message=f"Processed {len(request.urls)} URLs successfully",
            downloaded_files=download_result["downloaded_files"],
            transcriptions=transcription_result["transcriptions"],
            claims=all_claims,
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

@router.post("/extract-claims")
async def extract_claims():
    """Extract claims from existing transcriptions"""
    try:
        transcriber = TranscriptionService()
        transcription_result = transcriber.transcribe_audio_files()
        
        all_claims = []
        for transcription in transcription_result["transcriptions"]:
            if transcription["success"]:
                claims = extract_claims_from_transcript(transcription["transcription"])
                all_claims.extend(claims)
        
        return {
            "success": True,
            "total_claims": len(all_claims),
            "claims": all_claims
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))