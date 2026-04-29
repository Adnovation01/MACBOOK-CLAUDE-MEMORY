import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from typing import List
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin

_H = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

class YelpPlugin(BasePlugin):
    name = "yelp"
    requires_auth = False
    rate_limit_seconds = 4.0

    def health_check(self) -> dict:
        try:
            r = requests.get('https://www.yelp.com/search?find_desc=test&find_loc=Austin+TX',
                             timeout=8, headers=_H, allow_redirects=True)
            if r.status_code == 403 or 'enable JS' in r.text or 'cf-browser-verification' in r.text:
                return {"status": "degraded", "error": "Cloudflare bot protection active — search results blocked"}
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
            url = f"https://www.yelp.com/search?find_desc={quote(keyword)}&find_loc={quote(location)}"
            r = requests.get(url, headers=_H, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            for item in soup.select('h3 a[href*="/biz/"]')[:max_leads]:
                name = item.get_text(strip=True)
                if name:
                    leads.append(Lead(business_name=name, website='https://www.yelp.com' + item['href'], city=city, state=state, sources=['yelp']))
        except Exception:
            pass
        return leads
