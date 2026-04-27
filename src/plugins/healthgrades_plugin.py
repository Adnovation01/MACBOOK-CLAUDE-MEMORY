import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from typing import List
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin

_H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

class HealthgradesPlugin(BasePlugin):
    name = "healthgrades"
    requires_auth = False
    rate_limit_seconds = 3.0

    def search(self, keyword: str, location: str, max_leads: int) -> List[Lead]:
        leads = []
        city = location.split(',')[0].strip()
        state = location.split(',')[1].strip() if ',' in location else ''
        try:
            url = f"https://www.healthgrades.com/usearch?what={quote(keyword)}&where={quote(location)}"
            r = requests.get(url, headers=_H, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.select('a.provider-name')[:max_leads]:
                name = a.get_text(strip=True)
                href = a.get('href', '')
                if name:
                    leads.append(Lead(business_name=name, website=f"https://www.healthgrades.com{href}", city=city, state=state, sources=['healthgrades']))
        except Exception:
            pass
        return leads
