import re
from youtube_transcript_api import YouTubeTranscriptApi


class YouTubeLoader:

    @staticmethod
    def extract_video_id(url):

        patterns = [
            r"v=([a-zA-Z0-9_-]{11})",
            r"youtu\.be/([a-zA-Z0-9_-]{11})"
        ]

        for pattern in patterns:
            match = re.search(pattern, url)

            if match:
                return match.group(1)

        return None

    @staticmethod
    def get_transcript(url):

        video_id = YouTubeLoader.extract_video_id(url)

        ytt_api = YouTubeTranscriptApi()

        fetched_transcript = ytt_api.fetch(video_id)

        text = " ".join(
            snippet.text
            for snippet in fetched_transcript
        )

        return text