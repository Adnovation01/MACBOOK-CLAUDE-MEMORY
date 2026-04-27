from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import List, Optional

@dataclass
class Lead:
    business_name: str = ""
    website: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    facebook_url: str = ""
    instagram_handle: str = ""
    linkedin_url: str = ""
    twitter_handle: str = ""
    youtube_channel: str = ""
    review_count: int = 0
    avg_rating: float = 0.0
    review_platform: str = ""
    reddit_mentions: List[str] = field(default_factory=list)
    runs_google_ads: bool = False
    runs_fb_ads: bool = False
    pain_points: List[str] = field(default_factory=list)
    intent_score: int = 0
    recent_negative_reviews: List[str] = field(default_factory=list)
    unanswered_reviews: int = 0
    website_issues: List[str] = field(default_factory=list)
    no_social_presence: bool = False
    competitor_advantage: str = ""
    last_ad_seen: Optional[date] = None
    hook_1: str = ""
    hook_2: str = ""
    best_contact_time: str = ""
    email_subject_angle: str = ""
    sources: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    scraped_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        d = asdict(self)
        d['scraped_at'] = self.scraped_at.isoformat()
        if self.last_ad_seen:
            d['last_ad_seen'] = self.last_ad_seen.isoformat()
        return d
