import os
import requests
import json
import sys
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import datetime

from services.video_downloader_service import VideoDownloaderService
from services.transcription_service import TranscriptionService
from models.video import Video
from databases import get_session

# Import RAG utilities
rag_utils_path = '/project/rag'  # ✅ Use mounted project path
sys.path.append(rag_utils_path)
# print(f"🔎 Attempting to import utils from: {rag_utils_path}")
try:
    from utils import get_chroma_collection, get_source_name_from_url
    RAG_AVAILABLE = True
    print("✅ RAG utilities imported successfully")
except ImportError as e:
    RAG_AVAILABLE = False
    print(f"⚠️ RAG utilities not available: {e}")
    # print(f"   RAG path exists: {os.path.exists(rag_utils_path)}")
    # print(f"   Utils file exists: {os.path.exists(os.path.join(rag_utils_path, 'utils.py'))}")

def get_db():
    session_gen = get_session()
    return next(session_gen)  # Extract Session from generator


def translate_to_english(arabic_text):
    """Translate Arabic text to English for ChromaDB querying"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️ No API key for translation, using original text")
            return arabic_text  # Fallback to original
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        prompt = f"""
Translate this Arabic medical text to English. Only return the English translation, no other text or explanations:

{arabic_text}
"""
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            candidates = response_data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    english_text = parts[0].get("text", "").strip()
                    print(f"🔄 Translated: '{arabic_text}' → '{english_text}'")
                    return english_text
        
        print(f"⚠️ Translation failed, using original text")
        return arabic_text  # Fallback to original
        
    except Exception as e:
        print(f"❌ Translation error: {e}")
        return arabic_text  # Fallback to original


def get_relevant_context(claim, max_results=3):
    """Retrieve relevant documents from ChromaDB for fact-checking context"""
    try:
        if not RAG_AVAILABLE:
            print("⚠️ RAG not available, proceeding without context")
            return []

        # ✅ Translate Arabic claim to English for better retrieval
        english_claim = translate_to_english(claim)
        print(f"🔍 Querying ChromaDB with: '{english_claim}'")

        # Get the ChromaDB collection
        collection = get_chroma_collection()
        
        # Query for relevant documents using English translation
        results = collection.query(
            query_texts=[english_claim],  # ✅ Use translated text
            n_results=max_results
        )
        
        relevant_docs = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                distance = results['distances'][0][i] if results['distances'] else 1.0
                metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                
                # ✅ Simple relevance calculation for internal sorting only
                relevance_score = max(0, 1 - distance)  # Ensure non-negative, just for sorting
                
                relevant_docs.append({
                    'content': doc,
                    'relevance_score': relevance_score,  # ✅ Only for internal sorting
                    'distance': distance,                # ✅ Raw distance for debugging
                    'metadata': metadata  # ✅ Include metadata (contains source_url)
                })
                print(f"📄 Retrieved relevant doc {i+1} (distance: {distance:.3f})")
        
        return relevant_docs
        
    except Exception as e:
        print(f"⚠️ Error retrieving relevant context: {e}")
        return []


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
    """Extract diabetes claims from transcript - Returns only claims"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️ Warning: GEMINI_API_KEY not found, skipping claim extraction")
            return []

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

        prompt = f"""
You are an expert medical claim extractor for an "AI MythBuster" project. Your task is to analyze the provided video transcript to identify and extract factual claims ONLY.

You must follow these rules strictly:
1. The transcript may contain spelling errors, grammar mistakes, and conversational fillers. Ignore these errors and focus on understanding the intended meaning of the text.
2. Read the transcript carefully to determine if the primary topic and claims are related to the medical field of "Diabetes" or diabetic care.
3. If the transcript's claims are NOT about Diabetes, your output MUST be this exact JSON object:
   {{"domain_is_diabetes": false, "claims": []}}

4. If the transcript's claims ARE about Diabetes, identify the main claims.
   - Prioritize extracting any claims that are likely to be medically misleading, exaggerated, or incorrect. If no such claims are found, then extract up to three significant factual claims. All claims must be written in correct Arabic, clearly and objectively, while preserving the speaker's original intended meaning without softening or interpreting it.
   - Focus on the single most significant claim if possible.
   - If a single main claim cannot be identified, extract up to a maximum of three distinct, verifiable claims.
   - Each claim should be a concise, objective statement written in Arabic language.

5. Your output MUST be this exact JSON format, with the boolean value and claims array filled in based on the rules above. All claims must be written in Arabic. Do not include any other text, explanations, or conversational language.

{{
  "domain_is_diabetes": true,
  "claims": [
    "Arabic claim text 1",
    "Arabic claim text 2",
    "Arabic claim text 3"
  ]
}}

Transcript to analyze:
"{transcript_text}"
"""

        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        headers = {"Content-Type": "application/json"}

        # Add retry logic for API overload
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=60)
                
                if response.status_code == 200:
                    break
                elif response.status_code == 503:
                    print(f"⚠️ Gemini API overloaded (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay} seconds...")
                    if attempt < max_retries - 1:  # Don't sleep on last attempt
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                else:
                    print(f"❌ Gemini API error: {response.status_code} - {response.text}")
                    return []
            except requests.exceptions.RequestException as e:
                print(f"❌ Request error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return []

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
                            claims = parsed_response.get("claims", [])
                            print(f"✅ Diabetes video detected. Claims: {len(claims)}")
                            return claims
                        else:
                            print("ℹ️ Video is not about diabetes, skipping claim extraction")
                            return []

                    except json.JSONDecodeError:
                        print(f"❌ Failed to parse JSON response: {extracted_text}")
                        # Fallback: extract claims without verdicts
                        claims = [
                            claim.strip()
                            for claim in extracted_text.split("\n")
                            if claim.strip()
                        ]
                        return claims[:3]

            return []
        else:
            print(f"❌ Gemini API error: {response.status_code} - {response.text}")
            return []

    except Exception as e:
        print(f"❌ Error extracting claims: {str(e)}")
        return []


def fact_check_claims(claims):
    """Fact-check a list of diabetes claims using Gemini by processing each claim individually"""
    try:
        if not claims:
            return []

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️ Warning: GEMINI_API_KEY not found, skipping fact-checking")
            return []

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        all_verdicts = []
        
        # Process each claim individually
        for i, claim in enumerate(claims):
            print(f"🔍 Fact-checking claim {i+1}/{len(claims)}: {claim[:50]}...")
            
            verdict = fact_check_single_claim(claim, api_key, url)
            if verdict:
                all_verdicts.append(verdict)
        
        print(f"✅ Fact-checked {len(all_verdicts)} claims successfully")
        return all_verdicts

    except Exception as e:
        print(f"❌ Error fact-checking claims: {str(e)}")
        return []


def fact_check_single_claim(claim, api_key, url):
    """Fact-check a single diabetes claim using Gemini with RAG context"""
    try:
        # Get relevant context from ChromaDB
        print(f"🔍 Retrieving relevant context for claim...")
        relevant_docs = get_relevant_context(claim)
        
        # Build context section for the prompt
        context_section = ""
        if relevant_docs:
            context_section = "\n\nRELEVANT MEDICAL KNOWLEDGE:\n"
            for i, doc in enumerate(relevant_docs):
                context_section += f"Document {i+1} (relevance: {doc['relevance_score']:.2f}):\n{doc['content']}\n\n"
            print(f"✅ Added {len(relevant_docs)} relevant documents as context")
        else:
            print("⚠️ No relevant context found, using general medical knowledge")
        
        prompt = f"""
You are an expert medical fact-checker for diabetes claims. Your task is to fact-check the provided diabetes claim using both your medical knowledge and the relevant medical literature provided below.

For the claim provided, you must evaluate its medical accuracy and provide:
1. verdict: TRUE, FALSE, PARTIALLY_TRUE, or INSUFFICIENT_INFO
2. confidence: A number between 0.0 and 1.0 indicating your confidence in the verdict
3. reasoning: Brief medical explanation in Arabic for your verdict
4. medical_category: One of: treatment, prevention, symptoms, causes, diet, lifestyle

Verdict definitions:
- TRUE: Medically accurate based on established diabetes knowledge
- FALSE: Medically incorrect or contradicts established knowledge  
- PARTIALLY_TRUE: Contains some truth but incomplete/misleading
- INSUFFICIENT_INFO: Cannot determine accuracy with available medical knowledge

IMPORTANT: Use the relevant medical knowledge provided below to inform your fact-checking. If the provided documents contain information that supports or contradicts the claim, reference this in your reasoning.{context_section}

Your output MUST be this exact JSON format. Do not include any other text, explanations, or conversational language.

{{
  "claim": "The original claim text",
  "verdict": "TRUE|FALSE|PARTIALLY_TRUE|INSUFFICIENT_INFO",
  "confidence": 0.85,
  "reasoning": "Brief medical explanation in Arabic",
  "medical_category": "treatment|prevention|symptoms|causes|diet|lifestyle"
}}

Claim to fact-check:
{claim}
"""

        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {"Content-Type": "application/json"}

        # Add retry logic for API overload
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=60)
                
                if response.status_code == 200:
                    break
                elif response.status_code == 503:
                    print(f"⚠️ Gemini API overloaded during fact-check (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay} seconds...")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                else:
                    print(f"❌ Gemini API error during fact-checking: {response.status_code} - {response.text}")
                    return None
            except requests.exceptions.RequestException as e:
                print(f"❌ Request error during fact-check (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return None

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

                        verdict = json.loads(extracted_text)
                        
                        # ✅ Add source information to the verdict
                        if relevant_docs:
                            # Build sources array with user-friendly relevance labels only (no percentages)
                            if relevant_docs:
                                verdict['sources'] = []
                                seen_urls = set()
                                for doc in relevant_docs:
                                    source_url = (doc.get('metadata') or {}).get('source_url')
                                    if source_url in seen_urls:
                                        continue
                                    seen_urls.add(source_url)
                                    current_position = len(verdict['sources'])
                                    relevance_display = (
                                        'Most Relevant' if current_position == 0 else 'Moderately Relevant' if current_position == 1 else 'Supporting Evidence'
                                    )
                                    relevance_badge = (
                                        'primary' if current_position == 0 else 'secondary' if current_position == 1 else 'tertiary'
                                    )
                                    # Assemble source info (exclude any numeric relevance fields)
                                    source_name, source_homepage = get_source_name_from_url(source_url)
                                    source_info = {
                                        'content_preview': doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content'],
                                        'relevance_display': relevance_display,
                                        'relevance_badge': relevance_badge,
                                        'source_type': 'medical_literature',
                                        'source_name': source_name,
                                        'source_url': source_url,
                                        'source_homepage': source_homepage,
                                    }
                                    verdict['sources'].append(source_info)
                        
                        print(f"✅ Fact-checked claim with RAG: {verdict.get('verdict', 'UNKNOWN')} using {len(verdict.get('sources', []))} unique sources")
                        return verdict

                    except json.JSONDecodeError:
                        print(f"❌ Failed to parse fact-check JSON response: {extracted_text}")
                        return None

            return None
        else:
            print(f"❌ Gemini API error during fact-checking: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error fact-checking single claim: {str(e)}")
        return None


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
            print(f"🔍 Extracting claims from: {transcription['filename']}")
            claims = extract_claims_from_transcript(transcription["transcription"])
            
            if claims:
                print(f"🔍 Fact-checking {len(claims)} claims individually")
                verdicts = fact_check_claims(claims)
                print(f"✅ Successfully fact-checked {len(verdicts)} out of {len(claims)} claims")

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
