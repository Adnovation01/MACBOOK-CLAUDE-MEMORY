import time
import requests
from urllib.parse import quote
from typing import List
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin

_HC_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

class YellowPagesPlugin(BasePlugin):
    name = "yellowpages"
    requires_auth = False
    rate_limit_seconds = 3.0

    def is_available(self) -> bool:
        return PLAYWRIGHT_AVAILABLE

    def health_check(self) -> dict:
        try:
            r = requests.head('https://www.yellowpages.com', timeout=5,
                              headers=_HC_HEADERS, allow_redirects=True)
            if r.status_code < 500:
                return {"status": "healthy", "error": None}
            return {"status": "failed", "error": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"status": "failed", "error": str(e)[:120]}

    def search(self, keyword: str, location: str, max_leads: int) -> List[Lead]:
        leads = []
        city = location.split(',')[0].strip()
        state = location.split(',')[1].strip() if ',' in location else ''
        pages_needed = (max_leads // 10) + 1
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers({'User-Agent': _UA})
                for pg in range(1, pages_needed + 1):
                    if len(leads) >= max_leads:
                        break
                    url = f"https://www.yellowpages.com/search?search_terms={quote(keyword)}&geo_location_terms={quote(city)}%2C+{quote(state)}&page={pg}"
                    try:
                        page.goto(url, wait_until='domcontentloaded', timeout=25000)
                        page.wait_for_selector('.result', timeout=8000)
                        for r in page.query_selector_all('.result'):
                            name_el = r.query_selector('.business-name')
                            url_el = r.query_selector('a.track-visit-website')
                            if name_el:
                                leads.append(Lead(
                                    business_name=name_el.inner_text().strip(),
                                    website=url_el.get_attribute('href') if url_el else '',
                                    city=city, state=state,
                                    sources=['yellowpages']
                                ))
                        time.sleep(1)
                    except Exception:
                        break
                browser.close()
        except Exception:
            pass
        return leads[:max_leads]
