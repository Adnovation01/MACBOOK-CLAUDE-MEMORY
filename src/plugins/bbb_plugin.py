import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from typing import List
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin

_H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

class BBBPlugin(BasePlugin):
    name = "bbb"
    requires_auth = False
    rate_limit_seconds = 3.0

    def health_check(self) -> dict:
        try:
            r = requests.head('https://www.bbb.org', timeout=5,
                              headers=_H, allow_redirects=True)
            if r.status_code < 500:
                return {"status": "healthy", "error": None}
            return {"status": "failed", "error": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"status": "failed", "error": str(e)[:120]}

    def search(self, keyword: str, location: str, max_leads: int) -> List[Lead]:
        leads = []
        city = location.split(',')[0].strip()
        state = location.split(',')[1].strip() if ',' in location else ''
        try:
            url = f"https://www.bbb.org/search?find_text={quote(keyword)}&find_loc={quote(location)}"
            r = requests.get(url, headers=_H, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            for card in soup.select('a.bds-h4')[:max_leads]:
                name = card.get_text(strip=True)
                href = card.get('href', '')
                if name:
                    leads.append(Lead(business_name=name, website=f"https://www.bbb.org{href}", city=city, state=state, sources=['bbb']))
        except Exception:
            pass
        return leads
