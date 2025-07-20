# import os
# import requests
# import json
# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from typing import List
# from services.video_downloader_service import VideoDownloaderService
# from services.transcription_service import TranscriptionService

# router = APIRouter()

# # ✅ Change to single video
# class VideoProcessRequest(BaseModel):
#     url: str  # Single URL instead of List[str]

# # ✅ Update response model for single video
# class VideoProcessResponse(BaseModel):
#     success: bool
#     message: str
#     downloaded_file: str      # Single file instead of List[str]
#     transcription: dict       # Single transcription instead of List[dict]
#     claims: List[str]         # Arabic claims
#     errors: List[str]

# def extract_claims_from_transcript(transcript_text):
#     """Extract diabetes claims using specialized Gemini prompt - Returns Arabic claims"""
#     try:
#         api_key = os.getenv("GEMINI_API_KEY")
#         if not api_key:
#             print("⚠️ Warning: GEMINI_API_KEY not found, skipping claim extraction")
#             return []
        
#         url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
#         # ✅ Update prompt to request Arabic claims
#         prompt = f"""
# You are an expert medical fact-checker for an "AI MythBuster" project. Your task is to analyze the provided video transcript to identify and extract factual claims.

# You must follow these rules strictly:
# 1.  The transcript may contain spelling errors, grammar mistakes, and conversational fillers. Ignore these errors and focus on understanding the intended meaning of the text.
# 2.  Read the transcript carefully to determine if the primary topic and claims are related to the medical field of "Diabetes" or diabetic care.
# 3.  If the transcript's claims are NOT about Diabetes, your output MUST be this exact JSON object:
#     {{"domain_is_diabetes": false, "claims": []}}
# 4.  If the transcript's claims ARE about Diabetes, identify the main claims.
#     - Focus on the single most significant claim if possible.
#     - If a single main claim cannot be identified, extract up to a maximum of three distinct, verifiable claims.
#     - Each claim should be a concise, objective statement written in Arabic language.

# 5.  Your output MUST be this exact JSON format, with the boolean value and claims array filled in based on the rules above. All claims must be written in Arabic. Do not include any other text, explanations, or conversational language.

# Transcript to analyze:
# "{transcript_text}"
#         """
        
#         payload = {
#             "contents": [
#                 {
#                     "parts": [
#                         {
#                             "text": prompt
#                         }
#                     ]
#                 }
#             ]
#         }
        
#         headers = {
#             'Content-Type': 'application/json'
#         }

#         response = requests.post(url, json=payload, headers=headers, timeout=30)
        
#         if response.status_code == 200:
#             response_data = response.json()
#             candidates = response_data.get('candidates', [])
#             if candidates:
#                 content = candidates[0].get('content', {})
#                 parts = content.get('parts', [])
#                 if parts:
#                     extracted_text = parts[0].get('text', '').strip()
                    
#                     try:
#                         # Remove any markdown formatting if present
#                         if extracted_text.startswith('```json'):
#                             extracted_text = extracted_text.replace('```json', '').replace('```', '').strip()
                        
#                         # Parse the JSON response
#                         parsed_response = json.loads(extracted_text)
                        
#                         # Check if it's diabetes-related
#                         if parsed_response.get("domain_is_diabetes", False):
#                             print(f"✅ Diabetes video detected. Arabic claims: {parsed_response.get('claims', [])}")
#                             return parsed_response.get("claims", [])
#                         else:
#                             print("ℹ️ Video is not about diabetes, skipping claim extraction")
#                             return []
                            
#                     except json.JSONDecodeError:
#                         print(f"❌ Failed to parse JSON response: {extracted_text}")
#                         # Fallback to simple text parsing
#                         claims = [claim.strip() for claim in extracted_text.split('\n') if claim.strip()]
#                         return claims[:3]  # Limit to 3 claims
            
#             return []
#         else:
#             print(f"❌ Gemini API error: {response.status_code} - {response.text}")
#             return []
            
#     except Exception as e:
#         print(f"❌ Error extracting claims: {str(e)}")
#         return []

# # ✅ Change endpoint to singular and update for single video
# @router.post("/process-video", response_model=VideoProcessResponse)
# async def process_video(request: VideoProcessRequest):
#     """Download ONE video, transcribe it, and extract Arabic claims"""
#     try:
#         print(f"🚀 Processing single video: {request.url}")
        
#         # Step 1: Download single video
#         downloader = VideoDownloaderService()
#         download_result = downloader.download_videos([request.url])  # Convert to list for service
        
#         if not download_result["success"] or not download_result["downloaded_files"]:
#             raise HTTPException(status_code=400, detail="Failed to download video")
        
#         # Get the single downloaded file
#         downloaded_file = download_result["downloaded_files"][0]
#         print(f"📥 Downloaded: {downloaded_file}")
        
#         # Step 2: Transcribe ONLY the single file
#         transcriber = TranscriptionService()
#         transcription_result = transcriber.transcribe_audio_files([downloaded_file])

#         if not transcription_result["transcriptions"]:
#             raise HTTPException(status_code=500, detail="Failed to transcribe video")

#         # Get the single transcription
#         transcription = transcription_result["transcriptions"][0]
#         print(f"🎤 Transcribed: {transcription['filename']}")

#         # Step 3: Extract Arabic claims from the single transcription
#         claims = []
#         if transcription["success"]:
#             print(f"🔍 Extracting Arabic claims from: {transcription['filename']}")
#             claims = extract_claims_from_transcript(transcription["transcription"])
        
#         print(f"✅ Extracted {len(claims)} Arabic claims")

#         return VideoProcessResponse(
#             success=True,
#             message=f"Successfully processed video",
#             downloaded_file=downloaded_file,
#             transcription=transcription,
#             claims=claims,
#             errors=download_result["errors"] + transcription_result["errors"]
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# # Add endpoint to clean old files
# @router.delete("/clean-downloads")
# async def clean_downloads():
#     """Clean up all downloaded files"""
#     try:
#         transcriber = TranscriptionService()
#         result = transcriber.cleanup_audio_files()
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

import os
import requests
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.video_downloader_service import VideoDownloaderService
from services.transcription_service import TranscriptionService

router = APIRouter()

# ✅ Single video request model
class VideoProcessRequest(BaseModel):
    url: str  # Single URL instead of List[str]

# ✅ Single video response model
class VideoProcessResponse(BaseModel):
    success: bool
    message: str
    downloaded_file: str      # Single file instead of List[str]
    transcription: dict       # Single transcription instead of List[dict]
    claims: List[str]         # Arabic claims
    errors: List[str]

def extract_claims_from_transcript(transcript_text):
    """Extract diabetes claims using specialized Gemini prompt - Returns Arabic claims"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️ Warning: GEMINI_API_KEY not found, skipping claim extraction")
            return []
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        # ✅ Prompt requesting Arabic claims
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
    - Each claim should be a concise, objective statement written in Arabic language.

5.  Your output MUST be this exact JSON format, with the boolean value and claims array filled in based on the rules above. All claims must be written in Arabic. Do not include any other text, explanations, or conversational language.

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
                    
                    try:
                        # Remove any markdown formatting if present
                        if extracted_text.startswith('```json'):
                            extracted_text = extracted_text.replace('```json', '').replace('```', '').strip()
                        
                        # Parse the JSON response
                        parsed_response = json.loads(extracted_text)
                        
                        # Check if it's diabetes-related
                        if parsed_response.get("domain_is_diabetes", False):
                            print(f"✅ Diabetes video detected. Arabic claims: {parsed_response.get('claims', [])}")
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

# ✅ Main endpoint for single video processing
@router.post("/process-video", response_model=VideoProcessResponse)
async def process_video(request: VideoProcessRequest):
    """Download ONE video, transcribe it, and extract Arabic claims"""
    try:
        print(f"🚀 Processing single video: {request.url}")
        
        # Step 1: Download single video
        downloader = VideoDownloaderService()
        download_result = downloader.download_videos([request.url])
        print(f"📥 Download result: {download_result}")
        
        if not download_result["success"] or not download_result["downloaded_files"]:
            raise HTTPException(status_code=400, detail="Failed to download video")
        
        # Get the single downloaded file
        downloaded_file = download_result["downloaded_files"][0]
        print(f"📁 File to transcribe: {downloaded_file}")
        
        # Step 2: Transcribe ONLY the single file
        print(f"🎤 Starting transcription...")
        transcriber = TranscriptionService()
        transcription_result = transcriber.transcribe_audio_files([downloaded_file])
        print(f"🎤 Transcription result: {transcription_result}")

        if not transcription_result["transcriptions"]:
            raise HTTPException(status_code=500, detail="Failed to transcribe video")

        # Get the single transcription
        transcription = transcription_result["transcriptions"][0]
        print(f"🎤 Transcribed: {transcription['filename']}")

        # Step 3: Extract Arabic claims from the single transcription
        claims = []
        if transcription["success"]:
            print(f"🔍 Extracting Arabic claims from: {transcription['filename']}")
            claims = extract_claims_from_transcript(transcription["transcription"])
        
        print(f"✅ Extracted {len(claims)} Arabic claims")

        return VideoProcessResponse(
            success=True,
            message=f"Successfully processed video",
            downloaded_file=downloaded_file,
            transcription=transcription,
            claims=claims,
            errors=download_result["errors"] + transcription_result["errors"]
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