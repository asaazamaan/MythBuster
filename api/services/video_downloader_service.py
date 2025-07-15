

## 🔧 **Step 1: Create the Video Downloader Service**

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
            'outtmpl': os.path.join(self.output_dir, '%(title).200s.%(ext)s'),
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True,
            'match_filter': self.duration_filter,
            'progress_hooks': [self._progress_hook],
        }
        
        downloaded_files = []
        errors = []
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                for url in urls:
                    try:
                        ydl.download([url])
                        print(f"✅ Downloaded: {url}")
                    except Exception as e:
                        errors.append(f"❌ Failed to download {url}: {str(e)}")
                        
            # Get list of downloaded files
            audio_files = [f for f in os.listdir(self.output_dir) if f.endswith('.mp3')]
            
            return {
                "success": True,
                "downloaded_files": audio_files,
                "errors": errors,
                "total_urls": len(urls),
                "successful_downloads": len(audio_files)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "downloaded_files": [],
                "errors": errors
            }
    
    def _progress_hook(self, d):
        """Progress hook for download status"""
        if d['status'] == 'downloading':
            print(f"📥 Downloading: {d.get('filename', 'Unknown')}")
        elif d['status'] == 'finished':
            print(f"✅ Finished: {d.get('filename', 'Unknown')}")