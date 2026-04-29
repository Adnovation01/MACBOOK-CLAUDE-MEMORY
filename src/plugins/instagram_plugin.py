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

_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'

class InstagramPlugin(BasePlugin):
    name = "instagram"
    requires_auth = True
    rate_limit_seconds = 8.0

    def __init__(self, session_manager: SessionManager):
        self._sessions = session_manager

    def is_available(self) -> bool:
        return PLAYWRIGHT_AVAILABLE and self._sessions.is_authenticated('instagram')

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
        cookies = self._sessions.get_cookies('instagram')
        query = quote(keyword.replace(' ', ''))
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                ctx = browser.new_context(user_agent=_UA)
                ctx.add_cookies(cookies)
                page = ctx.new_page()
                page.goto(f"https://www.instagram.com/explore/tags/{query}/", wait_until='domcontentloaded', timeout=25000)
                time.sleep(3)
                for a in page.query_selector_all('article a')[:max_leads]:
                    try:
                        handle_el = a.query_selector('span')
                        handle = handle_el.inner_text().strip() if handle_el else ''
                        if handle:
                            leads.append(Lead(business_name=handle, instagram_handle=handle, city=city, state=state, sources=['instagram']))
                    except Exception:
                        continue
                browser.close()
        except Exception:
            pass
        return leads[:max_leads]
