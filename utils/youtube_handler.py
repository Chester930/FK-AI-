from youtube_transcript_api import YouTubeTranscriptApi
import requests
import re
import logging
import json

logger = logging.getLogger(__name__)

class YouTubeHandler:
    def __init__(self):
        self.transcript_cache = {}
    
    def get_video_id(self, url: str) -> str:
        """從 URL 中提取 YouTube 影片 ID"""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:be\/)([0-9A-Za-z_-]{11})',
            r'(?:embed\/)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_video_info(self, url: str) -> dict:
        """使用 oEmbed API 獲取影片資訊"""
        try:
            video_id = self.get_video_id(url)
            if not video_id:
                return None
                
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            response = requests.get(oembed_url)
            response.raise_for_status()
            
            data = response.json()
            return {
                'title': data.get('title', 'Unknown Title'),
                'author': data.get('author_name', 'Unknown Author')
            }
            
        except Exception as e:
            logger.error(f"獲取影片資訊時發生錯誤: {str(e)}")
            return None

    def get_transcript(self, url: str, lang: str = 'zh-TW') -> str:
        """獲取影片字幕"""
        try:
            video_id = self.get_video_id(url)
            if not video_id:
                return "無效的 YouTube URL"
                
            # 檢查快取
            if video_id in self.transcript_cache:
                return self.transcript_cache[video_id]
            
            # 獲取字幕
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            try:
                transcript = transcript_list.find_transcript([lang])
            except:
                try:
                    # 如果找不到指定語言的字幕，嘗試獲取自動生成的字幕
                    transcript = transcript_list.find_transcript(['zh-Hant'])
                except:
                    # 如果還是找不到，嘗試英文字幕
                    transcript = transcript_list.find_transcript(['en']).translate(lang)
            
            formatted_transcript = []
            for entry in transcript.fetch():
                text = entry['text']
                start_time = int(entry['start'])
                minutes = start_time // 60
                seconds = start_time % 60
                formatted_transcript.append(f"[{minutes:02d}:{seconds:02d}] {text}")
            
            result = "\n".join(formatted_transcript)
            
            # 儲存到快取
            self.transcript_cache[video_id] = result
            
            return result
            
        except Exception as e:
            logger.error(f"獲取 YouTube 字幕時發生錯誤: {str(e)}")
            return f"無法獲取字幕: {str(e)}" 