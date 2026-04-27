from difflib import SequenceMatcher
from typing import List, Optional
from src.models.lead import Lead

class Deduplicator:
    def __init__(self, similarity_threshold: float = 0.85, total_plugins: int = 27):
        self._threshold = similarity_threshold
        self._total_plugins = total_plugins

    def deduplicate(self, leads: List[Lead]) -> List[Lead]:
        merged: List[Lead] = []
        for lead in leads:
            match = self._find_match(lead, merged)
            if match is None:
                merged.append(lead)
            else:
                self._merge_into(match, lead)
        for lead in merged:
            lead.confidence_score = len(lead.sources) / self._total_plugins
        return merged

    def _find_match(self, lead: Lead, existing: List[Lead]) -> Optional[Lead]:
        for e in existing:
            if lead.website and e.website and lead.website == e.website:
                return e
            if lead.city == e.city and self._similar(lead.business_name, e.business_name):
                return e
        return None

    def _similar(self, a: str, b: str) -> bool:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= self._threshold

    def _merge_into(self, base: Lead, new: Lead):
        for attr in ['email', 'phone', 'website', 'facebook_url', 'instagram_handle',
                     'linkedin_url', 'twitter_handle', 'youtube_channel', 'address']:
            if not getattr(base, attr) and getattr(new, attr):
                setattr(base, attr, getattr(new, attr))
        if new.review_count > base.review_count:
            base.review_count = new.review_count
            base.avg_rating = new.avg_rating
            base.review_platform = new.review_platform
        base.pain_points = list(set(base.pain_points + new.pain_points))
        base.reddit_mentions = list(set(base.reddit_mentions + new.reddit_mentions))
        base.sources = list(set(base.sources + new.sources))
        base.recent_negative_reviews = list(set(base.recent_negative_reviews + new.recent_negative_reviews))
        if not base.hook_1 and new.hook_1:
            base.hook_1 = new.hook_1
        if not base.hook_2 and new.hook_2:
            base.hook_2 = new.hook_2
