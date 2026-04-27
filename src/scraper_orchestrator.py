import concurrent.futures
import logging
from typing import List
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin
from src.deduplicator import Deduplicator
from src.website_enricher import WebsiteEnricher
from src.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

RATE_CONFIG = {
    'google_search': (8, 15), 'bing_search': (5, 10), 'duckduckgo': (3, 6),
    'google_maps': (8, 15), 'yellowpages': (3, 6), 'yelp': (3, 6),
    'facebook': (5, 10), 'instagram': (5, 10), 'linkedin': (5, 10),
    'twitter': (3, 6), 'youtube': (2, 4), 'reddit': (2, 2),
}

class ScraperOrchestrator:
    def __init__(self, plugins: List[BasePlugin]):
        self._plugins = [p for p in plugins if p.is_available()]
        self._deduplicator = Deduplicator(total_plugins=max(len(plugins), 1))
        self._enricher = WebsiteEnricher()
        self._rate_limiter = RateLimiter(RATE_CONFIG)

    def scrape(self, keyword: str, location: str, max_leads: int = 50) -> List[Lead]:
        if not self._plugins:
            return []
        per_plugin = max(5, max_leads // len(self._plugins))
        all_leads: List[Lead] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self._plugins)) as ex:
            futures = {
                ex.submit(self._run_plugin, p, keyword, location, per_plugin): p.name
                for p in self._plugins
            }
            for future in concurrent.futures.as_completed(futures):
                plugin_name = futures[future]
                try:
                    leads = future.result(timeout=120)
                    all_leads.extend(leads)
                    logger.info(f"{plugin_name}: {len(leads)} leads")
                except Exception as e:
                    logger.warning(f"{plugin_name} failed: {e}")

        merged = self._deduplicator.deduplicate(all_leads)
        enriched = [self._enricher.enrich(lead) for lead in merged]
        return self._score(enriched)[:max_leads]

    def _run_plugin(self, plugin: BasePlugin, keyword: str, location: str, max_leads: int) -> List[Lead]:
        self._rate_limiter.wait(plugin.name)
        return plugin.search(keyword, location, max_leads)

    def _score(self, leads: List[Lead]) -> List[Lead]:
        for lead in leads:
            score = 0
            if lead.recent_negative_reviews:
                score += 25
            if lead.unanswered_reviews > 0:
                score += 20
            if 'no_contact_or_booking_form' in lead.website_issues:
                score += 15
            if lead.competitor_advantage:
                score += 15
            if lead.no_social_presence:
                score += 10
            lead.intent_score = min(score, 100)
        return sorted(leads, key=lambda l: l.intent_score, reverse=True)
