import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from typing import List
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin

STATE_SEARCH_URLS = {
    'TX': 'https://mycpa.cpa.state.tx.us/coa/Index.do#search={keyword}',
    'CA': 'https://bizfileonline.sos.ca.gov/search/business?SearchType=&SearchValue={keyword}',
    'FL': 'https://search.sunbiz.org/Inquiry/CorporationSearch/ByName?inquiryDirective=ByName&searchNameOrder={keyword}',
    'NY': 'https://apps.dos.ny.gov/publicInquiry/#search&keyword={keyword}',
}

_H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

class StateRegistryPlugin(BasePlugin):
    name = "state_registry"
    requires_auth = False
    rate_limit_seconds = 4.0

    def search(self, keyword: str, location: str, max_leads: int) -> List[Lead]:
        leads = []
        city = location.split(',')[0].strip()
        state = location.split(',')[1].strip() if ',' in location else ''
        if state not in STATE_SEARCH_URLS:
            return leads
        try:
            url = STATE_SEARCH_URLS[state].format(keyword=quote(keyword))
            r = requests.get(url, headers=_H, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.find_all('a', string=lambda t: t and keyword.lower() in t.lower())[:max_leads]:
                name = a.get_text(strip=True)
                if name:
                    leads.append(Lead(business_name=name, city=city, state=state, sources=['state_registry']))
        except Exception:
            pass
        return leads
