import re
import json
import requests
from urllib.parse import quote
from typing import List
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin

_H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

class YouTubePlugin(BasePlugin):
    name = "youtube"
    requires_auth = False
    rate_limit_seconds = 3.0

    def search(self, keyword: str, location: str, max_leads: int) -> List[Lead]:
        leads = []
        city = location.split(',')[0].strip()
        state = location.split(',')[1].strip() if ',' in location else ''
        query = quote(f"{keyword} {city}")
        try:
            url = f"https://www.youtube.com/results?search_query={query}&sp=EgIQAg%3D%3D"
            r = requests.get(url, headers=_H, timeout=15)
            data_match = re.search(r'var ytInitialData = ({.*?});\s*</script>', r.text, re.DOTALL)
            if not data_match:
                return leads
            data = json.loads(data_match.group(1))
            contents = (data.get('contents', {})
                        .get('twoColumnSearchResultsRenderer', {})
                        .get('primaryContents', {})
                        .get('sectionListRenderer', {})
                        .get('contents', []))
            for section in contents:
                for item in section.get('itemSectionRenderer', {}).get('contents', []):
                    channel = item.get('channelRenderer', {})
                    name = channel.get('title', {}).get('simpleText', '')
                    url_path = (channel.get('navigationEndpoint', {})
                                .get('commandMetadata', {})
                                .get('webCommandMetadata', {})
                                .get('url', ''))
                    if name:
                        leads.append(Lead(business_name=name, youtube_channel=f"https://www.youtube.com{url_path}", city=city, state=state, sources=['youtube']))
                        if len(leads) >= max_leads:
                            break
        except Exception:
            pass
        return leads[:max_leads]
