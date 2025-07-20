import os
from yt_dlp import YoutubeDL
from typing import List, Dict, Any

class VideoDownloaderService:
    def __init__(self, output_dir: str = "downloads"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def duration_filter(self, info):
        """Filter videos longer than 2 minutes"""
        duration = info.get("duration", 0)
        if duration >= 120:
            return f"Skipping video (duration too long): {duration}s"
        return None

    def download_videos(self, urls: List[str]) -> Dict[str, Any]:
        """Download videos and return results"""
        ydl_opts = {
            "outtmpl": os.path.join(self.output_dir, "%(title)s.%(ext)s"),
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "noplaylist": True,
            "match_filter": self.duration_filter,
            "restrictfilenames": True,
        }

        downloaded_files = []
        errors = []

        try:
            with YoutubeDL(ydl_opts) as ydl:
                for url in urls:
                    try:
                        # Download the video
                        ydl.download([url])
                        print(f"✅ Downloaded: {url}")
                        
                        # ✅ Simple approach: Get the newest MP3 file
                        mp3_files = [f for f in os.listdir(self.output_dir) if f.endswith('.mp3')]
                        
                        if mp3_files:
                            # Get the most recently modified MP3 file
                            newest_file = max(mp3_files, key=lambda f: os.path.getmtime(os.path.join(self.output_dir, f)))
                            downloaded_files.append(newest_file)
                            print(f"📁 Found downloaded file: {newest_file}")
                        else:
                            errors.append(f"No MP3 file found after downloading {url}")

                    except Exception as e:
                        errors.append(f"❌ Failed to download {url}: {str(e)}")

            return {
                "success": len(downloaded_files) > 0,
                "downloaded_files": downloaded_files,
                "errors": errors,
                "total_urls": len(urls),
                "successful_downloads": len(downloaded_files),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "downloaded_files": [],
                "errors": errors,
            }