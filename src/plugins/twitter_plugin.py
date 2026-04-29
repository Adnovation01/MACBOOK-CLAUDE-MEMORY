import time
from urllib.parse import quote
from typing import List
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin
from src.session_manager import SessionManager

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

class TwitterPlugin(BasePlugin):
    name = "twitter"
    requires_auth = True
    rate_limit_seconds = 6.0

    def __init__(self, session_manager: SessionManager):
        self._sessions = session_manager

    def is_available(self) -> bool:
        return PLAYWRIGHT_AVAILABLE and self._sessions.is_authenticated('twitter')

    def health_check(self) -> dict:
        if not self._sessions.is_authenticated(self.name):
            return {"status": "degraded", "error": "missing credentials — add session via Settings"}
        return {"status": "healthy", "error": None}

    def search(self, keyword: str, location: str, max_leads: int) -> List[Lead]:
        if not self.is_available():
            return []
        leads = []
        city = location.split(',')[0].strip()
        state = location.split(',')[1].strip() if ',' in location else ''
        cookies = self._sessions.get_cookies('twitter')
        query = quote(f"{keyword} {city}")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                ctx = browser.new_context(user_agent=_UA)
                ctx.add_cookies(cookies)
                page = ctx.new_page()
                page.goto(f"https://twitter.com/search?q={query}&f=user", wait_until='domcontentloaded', timeout=25000)
                time.sleep(3)
                for card in page.query_selector_all('div[data-testid="UserCell"]')[:max_leads]:
                    try:
                        name_el = card.query_selector('span.css-901oao')
                        if name_el:
                            leads.append(Lead(business_name=name_el.inner_text().strip(), city=city, state=state, sources=['twitter']))
                    except Exception:
                        continue
                browser.close()
        except Exception:
            pass
        return leads[:max_leads]
