import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from typing import List
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin

_H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

class TrustpilotPlugin(BasePlugin):
    name = "trustpilot"
    requires_auth = False
    rate_limit_seconds = 3.0

    def search(self, keyword: str, location: str, max_leads: int) -> List[Lead]:
        leads = []
        city = location.split(',')[0].strip()
        state = location.split(',')[1].strip() if ',' in location else ''
        try:
            url = f"https://www.trustpilot.com/search?query={quote(keyword)}+{quote(city)}"
            r = requests.get(url, headers=_H, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            for card in soup.select('div[data-business-unit-id]')[:max_leads]:
                name_el = card.select_one('p.title_displayName__TtDDM')
                rating_el = card.select_one('p[data-rating-typography]')
                if name_el:
                    lead = Lead(business_name=name_el.get_text(strip=True), city=city, state=state, sources=['trustpilot'])
                    if rating_el:
                        try:
                            lead.avg_rating = float(rating_el.get_text(strip=True))
                            lead.review_platform = 'trustpilot'
                        except ValueError:
                            pass
                    leads.append(lead)
        except Exception:
            pass
        return leads
