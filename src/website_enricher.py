import re
import requests
from bs4 import BeautifulSoup
from typing import Optional
from src.models.lead import Lead

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_RE = re.compile(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]')
INVALID_DOMAINS = {'wix.com', 'example.com', 'test.com', 'domain.com', 'sitedomain.com'}
INVALID_LOCAL = {'noreply', 'no-reply', 'donotreply'}
INVALID_ANYWHERE = {'sentry', '.png', '.jpg'}
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

class WebsiteEnricher:
    def enrich(self, lead: Lead) -> Lead:
        if not lead.website:
            return lead
        try:
            html = self._fetch(lead.website)
            if not html:
                return lead
            if not lead.email:
                lead.email = self._extract_email(html) or self._check_contact_page(lead.website) or ""
            if not lead.phone:
                lead.phone = self._extract_phone(html) or ""
            self._extract_socials(html, lead)
            self._detect_issues(html, lead)
        except Exception:
            pass
        return lead

    def _fetch(self, url: str) -> Optional[str]:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            return r.text
        except Exception:
            return None

    def _extract_email(self, html: str) -> Optional[str]:
        for m in EMAIL_RE.findall(html):
            local, _, domain = m.partition('@')
            if domain.lower() in INVALID_DOMAINS:
                continue
            if local.lower() in INVALID_LOCAL:
                continue
            if any(p in m.lower() for p in INVALID_ANYWHERE):
                continue
            return m
        return None

    def _extract_phone(self, html: str) -> Optional[str]:
        matches = PHONE_RE.findall(html)
        return matches[0].strip() if matches else None

    def _check_contact_page(self, base_url: str) -> Optional[str]:
        for path in ['/contact', '/contact-us', '/about']:
            html = self._fetch(base_url.rstrip('/') + path)
            if html:
                email = self._extract_email(html)
                if email:
                    return email
        return None

    def _extract_socials(self, html: str, lead: Lead):
        soup = BeautifulSoup(html, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'facebook.com' in href and not lead.facebook_url:
                lead.facebook_url = href
            elif 'instagram.com' in href and not lead.instagram_handle:
                lead.instagram_handle = href.split('instagram.com/')[-1].strip('/')
            elif 'linkedin.com/company' in href and not lead.linkedin_url:
                lead.linkedin_url = href
            elif ('twitter.com' in href or 'x.com' in href) and not lead.twitter_handle:
                lead.twitter_handle = href
            elif 'youtube.com' in href and not lead.youtube_channel:
                lead.youtube_channel = href

    def _detect_issues(self, html: str, lead: Lead):
        issues = []
        lower = html.lower()
        if 'contact' not in lower and 'book' not in lower and 'schedule' not in lower:
            issues.append('no_contact_or_booking_form')
        if lead.website and not lead.website.startswith('https://'):
            issues.append('no_ssl')
        if not lead.facebook_url and not lead.instagram_handle:
            lead.no_social_presence = True
        lead.website_issues = issues
