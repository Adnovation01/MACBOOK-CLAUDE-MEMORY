import time
import re
from urllib.parse import quote
from typing import List
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

class GoogleMapsPlugin(BasePlugin):
    name = "google_maps"
    requires_auth = False
    rate_limit_seconds = 8.0

    def is_available(self) -> bool:
        return PLAYWRIGHT_AVAILABLE

    def search(self, keyword: str, location: str, max_leads: int) -> List[Lead]:
        leads = []
        city = location.split(',')[0].strip()
        state = location.split(',')[1].strip() if ',' in location else ''
        query = quote(f"{keyword} {location}")
        url = f"https://www.google.com/maps/search/{query}"
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers({'User-Agent': _UA})
                page.goto(url, wait_until='domcontentloaded', timeout=25000)
                time.sleep(2)
                for _ in range(3):
                    page.keyboard.press('End')
                    time.sleep(1)
                for listing in page.query_selector_all('div[role="article"]')[:max_leads]:
                    try:
                        name_el = listing.query_selector('div.qBF1Pd')
                        rating_el = listing.query_selector('span.MW4etd')
                        review_el = listing.query_selector('span.UY7F9')
                        name = name_el.inner_text().strip() if name_el else ''
                        if not name:
                            continue
                        lead = Lead(business_name=name, city=city, state=state, sources=['google_maps'])
                        if rating_el:
                            try:
                                lead.avg_rating = float(rating_el.inner_text().strip())
                                lead.review_platform = 'google'
                            except ValueError:
                                pass
                        if review_el:
                            try:
                                lead.review_count = int(re.sub(r'[^\d]', '', review_el.inner_text()))
                            except ValueError:
                                pass
                        leads.append(lead)
                    except Exception:
                        continue
                browser.close()
        except Exception:
            pass
        return leads[:max_leads]
