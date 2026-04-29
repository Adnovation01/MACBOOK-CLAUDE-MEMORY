import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from typing import List
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin

BLOCKED = {'yelp.', 'facebook.', 'linkedin.', 'yellowpages.', 'healthgrades.', 'zocdoc.'}
_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

class DuckDuckGoPlugin(BasePlugin):
    name = "duckduckgo"
    requires_auth = False
    rate_limit_seconds = 3.0

    def health_check(self) -> dict:
        try:
            r = requests.head('https://html.duckduckgo.com', timeout=5,
                              headers=_HEADERS, allow_redirects=True)
            if r.status_code < 500:
                return {"status": "healthy", "error": None}
            return {"status": "failed", "error": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"status": "failed", "error": str(e)[:120]}

    def search(self, keyword: str, location: str, max_leads: int) -> List[Lead]:
        leads = []
        city = location.split(',')[0].strip()
        state = location.split(',')[1].strip() if ',' in location else ''
        query = quote(f"{keyword} {location} contact")
        url = f"https://html.duckduckgo.com/html/?q={query}"
        try:
            r = requests.get(url, headers=_HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.find_all('a', class_='result__a')[:max_leads]:
                href = a.get('href', '')
                if any(b in href for b in BLOCKED):
                    continue
                leads.append(Lead(
                    business_name=a.get_text(strip=True),
                    website=href,
                    city=city, state=state,
                    sources=['duckduckgo']
                ))
        except Exception:
            pass
        return leads
