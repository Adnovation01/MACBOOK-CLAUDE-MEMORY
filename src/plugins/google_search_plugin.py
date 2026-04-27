import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from typing import List
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin

BLOCKED = {'yelp.', 'facebook.', 'linkedin.', 'yellowpages.', 'healthgrades.', 'zocdoc.'}
_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'}

class GoogleSearchPlugin(BasePlugin):
    name = "google_search"
    requires_auth = False
    rate_limit_seconds = 10.0

    def search(self, keyword: str, location: str, max_leads: int) -> List[Lead]:
        leads = []
        city = location.split(',')[0].strip()
        state = location.split(',')[1].strip() if ',' in location else ''
        query = quote(f"{keyword} {location} email contact")
        url = f"https://www.google.com/search?q={query}&num=50"
        try:
            r = requests.get(url, headers=_HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            for div in soup.select('div.g')[:max_leads]:
                a = div.find('a')
                if not a:
                    continue
                href = a.get('href', '')
                h3 = div.find('h3')
                if not h3 or not href or href.startswith('/'):
                    continue
                if any(b in href for b in BLOCKED):
                    continue
                leads.append(Lead(
                    business_name=h3.get_text(strip=True),
                    website=href,
                    city=city, state=state,
                    sources=['google_search']
                ))
        except Exception:
            pass
        return leads
