import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from typing import List
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin

BLOCKED = {'yelp.', 'facebook.', 'linkedin.', 'yellowpages.', 'healthgrades.'}
_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

class BingSearchPlugin(BasePlugin):
    name = "bing_search"
    requires_auth = False
    rate_limit_seconds = 5.0

    def search(self, keyword: str, location: str, max_leads: int) -> List[Lead]:
        leads = []
        city = location.split(',')[0].strip()
        state = location.split(',')[1].strip() if ',' in location else ''
        query = quote(f"{keyword} {location} email contact")
        url = f"https://www.bing.com/search?q={query}&count=50"
        try:
            r = requests.get(url, headers=_HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            for li in soup.select('li.b_algo')[:max_leads]:
                a = li.find('a')
                if not a:
                    continue
                href = a.get('href', '')
                if any(b in href for b in BLOCKED):
                    continue
                leads.append(Lead(
                    business_name=a.get_text(strip=True),
                    website=href,
                    city=city, state=state,
                    sources=['bing_search']
                ))
        except Exception:
            pass
        return leads
