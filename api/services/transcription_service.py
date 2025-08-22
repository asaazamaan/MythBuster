import os
import time
from typing import List, Dict, Any

# OpenAI SDK (ensure `openai` is in requirements and OPENAI_API_KEY is in .env)
from openai import OpenAI


class TranscriptionService:
    def __init__(self, output_dir: str = "downloads"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Model can be overridden via env if you want to try `gpt-4o-transcribe`
        self.model = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")

        print(f"🚀 Initializing OpenAI transcription client (model={self.model})...")
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️ OPENAI_API_KEY is not set. Transcription calls will fail until it’s provided.")
        self.client = OpenAI()
        print("✅ OpenAI client ready!")

    def transcribe_audio_files(self, audio_files: List[str]) -> Dict[str, Any]:
        """Transcribe ONLY the specified files using OpenAI hosted Whisper."""
        if not audio_files:
            return {
                "transcriptions": [],
                "errors": ["No audio files provided"],
                "total_files": 0,
                "successful_transcriptions": 0,
            }

        # Keep the same behavior: only process .mp3 files that were explicitly passed in
        audio_files = [f for f in audio_files if f.endswith(".mp3")]
        print(f"🎯 Processing ONLY specified files: {audio_files}")

        transcriptions: List[Dict[str, Any]] = []
        errors: List[str] = []

        for audio_file in audio_files:
            file_path = os.path.join(self.output_dir, audio_file)

            try:
                if not os.path.exists(file_path):
                    err = f"File not found: {audio_file}"
                    errors.append(err)
                    print(f"❌ {err}")
                    continue

                print(f"🎤 Transcribing: {audio_file}")

                # Simple retry for transient network/API hiccups
                max_retries = 3
                delay = 5
                last_exc: Exception | None = None
                text: str = ""

                for attempt in range(max_retries):
                    try:
                        with open(file_path, "rb") as f:
                            resp = self.client.audio.transcriptions.create(
                                model=self.model,
                                file=f,
                            )
                        # OpenAI v1 client returns an object with `.text`
                        text = getattr(resp, "text", "") or ""
                        break
                    except Exception as e:
                        last_exc = e
                        print(
                            f"❌ OpenAI transcription error (attempt {attempt+1}/{max_retries}): {e}"
                        )
                        if attempt < max_retries - 1:
                            time.sleep(delay)
                            delay *= 2
                            continue

                if text:
                    transcriptions.append(
                        {
                            "filename": audio_file,
                            "transcription": text,
                            "success": True,
                            "file_size": os.path.getsize(file_path),
                        }
                    )
                    print(f"✅ Transcribed: {audio_file}")
                else:
                    err_msg = (
                        f"OpenAI transcription failed for {audio_file}: {last_exc}"
                        if last_exc
                        else f"OpenAI transcription failed for {audio_file}: Unknown error"
                    )
                    errors.append(err_msg)
                    transcriptions.append(
                        {
                            "filename": audio_file,
                            "transcription": "",
                            "success": False,
                            "error": str(last_exc) if last_exc else "Unknown error",
                        }
                    )

            except Exception as e:
                errors.append(f"Failed to transcribe {audio_file}: {str(e)}")
                transcriptions.append(
                    {
                        "filename": audio_file,
                        "transcription": "",
                        "success": False,
                        "error": str(e),
                    }
                )

        return {
            "transcriptions": transcriptions,
            "errors": errors,
            "total_files": len(audio_files),
            "successful_transcriptions": len(
                [t for t in transcriptions if t.get("success")]
            ),
        }

    def cleanup_audio_files(self) -> Dict[str, Any]:
        """Clean up audio files from downloads directory (unchanged)."""
        try:
            if not os.path.exists(self.output_dir):
                return {
                    "success": True,
                    "message": "No files to clean",
                    "deleted_files": [],
                }

            audio_files = [
                f for f in os.listdir(self.output_dir) if f.endswith(".mp3")
            ]
            deleted_files: List[str] = []

            for audio_file in audio_files:
                file_path = os.path.join(self.output_dir, audio_file)
                os.remove(file_path)
                deleted_files.append(audio_file)
                print(f"🗑️ Deleted: {audio_file}")

            return {
                "success": True,
                "message": f"Deleted {len(deleted_files)} files",
                "deleted_files": deleted_files,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "deleted_files": []}




# import os
# from transformers import pipeline
# from typing import List, Dict, Any

# class TranscriptionService:
#     def __init__(self, output_dir: str = "downloads"):
#         self.output_dir = output_dir
#         os.makedirs(self.output_dir, exist_ok=True)
        
#         # ✅ Use default HF cache location (will use volume)
#         print("🚀 Loading Whisper model for real transcription...")
#         self.asr_pipeline = pipeline(
#             "automatic-speech-recognition",
#             model="openai/whisper-medium",
#             chunk_length_s=30,
#             return_timestamps=False,
#             device="cpu"
#             # ✅ No custom cache_dir - uses default /root/.cache/huggingface
#         )
#         print("✅ Whisper model loaded successfully!")
    
#     def transcribe_audio_files(self, audio_files: List[str]) -> Dict[str, Any]:
#         """Real transcription using Whisper - ONLY for specified files"""
        
#         # ✅ Always require specific files - no scanning directory
#         if not audio_files:
#             return {
#                 "transcriptions": [],
#                 "errors": ["No audio files provided"],
#                 "total_files": 0,
#                 "successful_transcriptions": 0
#             }
        
#         # Filter to only .mp3 files that exist
#         audio_files = [f for f in audio_files if f.endswith('.mp3')]
#         print(f"🎯 Processing ONLY specified files: {audio_files}")
        
#         transcriptions = []
#         errors = []
        
#         for audio_file in audio_files:
#             try:
#                 file_path = os.path.join(self.output_dir, audio_file)
#                 if os.path.exists(file_path):
#                     print(f"🎤 Transcribing: {audio_file}")
                    
#                     result = self.asr_pipeline(
#                         file_path,
#                         generate_kwargs={
#                             "task": "transcribe",
#                             "language": None
#                         }
#                     )
                    
#                     transcriptions.append({
#                         "filename": audio_file,
#                         "transcription": result["text"],
#                         "success": True,
#                         "file_size": os.path.getsize(file_path)
#                     })
                    
#                     print(f"✅ Transcribed: {audio_file}")
#                 else:
#                     errors.append(f"File not found: {audio_file}")
                    
#             except Exception as e:
#                 errors.append(f"Failed to transcribe {audio_file}: {str(e)}")
#                 transcriptions.append({
#                     "filename": audio_file,
#                     "transcription": "",
#                     "success": False,
#                     "error": str(e)
#                 })
        
#         return {
#             "transcriptions": transcriptions,
#             "errors": errors,
#             "total_files": len(audio_files),
#             "successful_transcriptions": len([t for t in transcriptions if t["success"]])
#         }
    
#     def cleanup_audio_files(self) -> Dict[str, Any]:
#         """Clean up audio files from downloads directory"""
#         try:
#             if not os.path.exists(self.output_dir):
#                 return {"success": True, "message": "No files to clean", "deleted_files": []}
            
#             audio_files = [f for f in os.listdir(self.output_dir) if f.endswith('.mp3')]
#             deleted_files = []
            
#             for audio_file in audio_files:
#                 file_path = os.path.join(self.output_dir, audio_file)
#                 os.remove(file_path)
#                 deleted_files.append(audio_file)
#                 print(f"🗑️ Deleted: {audio_file}")
            
#             return {
#                 "success": True,
#                 "message": f"Deleted {len(deleted_files)} files",
#                 "deleted_files": deleted_files
#             }
            
#         except Exception as e:
#             return {
#                 "success": False,
#                 "error": str(e),
#                 "deleted_files": []
#             }