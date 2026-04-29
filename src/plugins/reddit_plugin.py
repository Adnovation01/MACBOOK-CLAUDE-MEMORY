import os
import requests
from typing import List
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin

class RedditPlugin(BasePlugin):
    name = "reddit"
    requires_auth = False
    rate_limit_seconds = 2.0

    def is_available(self) -> bool:
        return bool(os.environ.get('REDDIT_CLIENT_ID') and os.environ.get('REDDIT_CLIENT_SECRET'))

    def health_check(self) -> dict:
        try:
            r = requests.head('https://www.reddit.com', timeout=5,
                              headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=True)
            if r.status_code < 500:
                return {"status": "healthy", "error": None}
            return {"status": "failed", "error": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"status": "failed", "error": str(e)[:120]}

    def search(self, keyword: str, location: str, max_leads: int) -> List[Lead]:
        # Reddit enriches leads via pain points, not direct discovery
        return []

    def get_pain_points_for(self, business_name: str, city: str) -> List[str]:
        if not self.is_available():
            return []
        mentions = []
        try:
            import praw
            reddit = praw.Reddit(
                client_id=os.environ['REDDIT_CLIENT_ID'],
                client_secret=os.environ['REDDIT_CLIENT_SECRET'],
                user_agent='lead_scraper/1.0'
            )
            for sub in reddit.subreddit('all').search(f'"{business_name}" {city}', limit=10):
                text = sub.title + ' ' + (sub.selftext or '')
                if len(text.strip()) > 20:
                    mentions.append(text[:200])
        except Exception:
            pass
        return mentions
