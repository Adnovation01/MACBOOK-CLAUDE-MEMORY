import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from typing import List
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin

_H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

class ThumbtackPlugin(BasePlugin):
    name = "thumbtack"
    requires_auth = False
    rate_limit_seconds = 3.0

    def health_check(self) -> dict:
        try:
            r = requests.head('https://www.thumbtack.com', timeout=5,
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
            url = f"https://www.thumbtack.com/k/{quote(keyword.lower().replace(' ','-'))}/near/{quote(city.lower().replace(' ','-'))}-{quote(state.lower())}/"
            r = requests.get(url, headers=_H, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            for card in soup.select('div[data-test="pro-card"]')[:max_leads]:
                name_el = card.select_one('h3')
                if name_el:
                    leads.append(Lead(business_name=name_el.get_text(strip=True), city=city, state=state, sources=['thumbtack']))
        except Exception:
            pass
        return leads
