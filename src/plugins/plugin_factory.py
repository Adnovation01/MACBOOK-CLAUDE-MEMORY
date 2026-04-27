import json
from typing import List
from src.plugins.base_plugin import BasePlugin
from src.session_manager import SessionManager

def build_plugins(config_path: str = 'config/scraper_config.json') -> List[BasePlugin]:
    with open(config_path) as f:
        config = json.load(f)
    enabled = {k for k, v in config['plugins'].items() if v.get('enabled')}
    sm = SessionManager()
    plugins: List[BasePlugin] = []

    if 'duckduckgo' in enabled:
        from src.plugins.duckduckgo_plugin import DuckDuckGoPlugin
        plugins.append(DuckDuckGoPlugin())
    if 'bing_search' in enabled:
        from src.plugins.bing_search_plugin import BingSearchPlugin
        plugins.append(BingSearchPlugin())
    if 'google_search' in enabled:
        from src.plugins.google_search_plugin import GoogleSearchPlugin
        plugins.append(GoogleSearchPlugin())
    if 'google_maps' in enabled:
        from src.plugins.google_maps_plugin import GoogleMapsPlugin
        plugins.append(GoogleMapsPlugin())
    if 'yellowpages' in enabled:
        from src.plugins.yellowpages_plugin import YellowPagesPlugin
        plugins.append(YellowPagesPlugin())
    if 'yelp' in enabled:
        from src.plugins.yelp_plugin import YelpPlugin
        plugins.append(YelpPlugin())
    if 'bbb' in enabled:
        from src.plugins.bbb_plugin import BBBPlugin
        plugins.append(BBBPlugin())
    if 'manta' in enabled:
        from src.plugins.manta_plugin import MantaPlugin
        plugins.append(MantaPlugin())
    if 'superpages' in enabled:
        from src.plugins.superpages_plugin import SuperpagesPlugin
        plugins.append(SuperpagesPlugin())
    if 'hotfrog' in enabled:
        from src.plugins.hotfrog_plugin import HotfrogPlugin
        plugins.append(HotfrogPlugin())
    if 'whitepages' in enabled:
        from src.plugins.whitepages_plugin import WhitepagesPlugin
        plugins.append(WhitepagesPlugin())
    if 'foursquare' in enabled:
        from src.plugins.foursquare_plugin import FoursquarePlugin
        plugins.append(FoursquarePlugin())
    if 'cylex' in enabled:
        from src.plugins.cylex_plugin import CylexPlugin
        plugins.append(CylexPlugin())
    if 'clutch' in enabled:
        from src.plugins.clutch_plugin import ClutchPlugin
        plugins.append(ClutchPlugin())
    if 'brownbook' in enabled:
        from src.plugins.brownbook_plugin import BrownbookPlugin
        plugins.append(BrownbookPlugin())
    if 'facebook' in enabled:
        from src.plugins.facebook_plugin import FacebookPlugin
        plugins.append(FacebookPlugin(sm))
    if 'instagram' in enabled:
        from src.plugins.instagram_plugin import InstagramPlugin
        plugins.append(InstagramPlugin(sm))
    if 'linkedin' in enabled:
        from src.plugins.linkedin_plugin import LinkedInPlugin
        plugins.append(LinkedInPlugin(sm))
    if 'twitter' in enabled:
        from src.plugins.twitter_plugin import TwitterPlugin
        plugins.append(TwitterPlugin(sm))
    if 'youtube' in enabled:
        from src.plugins.youtube_plugin import YouTubePlugin
        plugins.append(YouTubePlugin())
    if 'reddit' in enabled:
        from src.plugins.reddit_plugin import RedditPlugin
        plugins.append(RedditPlugin())
    if 'trustpilot' in enabled:
        from src.plugins.trustpilot_plugin import TrustpilotPlugin
        plugins.append(TrustpilotPlugin())
    if 'healthgrades' in enabled:
        from src.plugins.healthgrades_plugin import HealthgradesPlugin
        plugins.append(HealthgradesPlugin())
    if 'angi' in enabled:
        from src.plugins.angi_plugin import AngiPlugin
        plugins.append(AngiPlugin())
    if 'thumbtack' in enabled:
        from src.plugins.thumbtack_plugin import ThumbtackPlugin
        plugins.append(ThumbtackPlugin())
    if 'opencorporates' in enabled:
        from src.plugins.opencorporates_plugin import OpenCorporatesPlugin
        plugins.append(OpenCorporatesPlugin())
    if 'state_registry' in enabled:
        from src.plugins.state_registry_plugin import StateRegistryPlugin
        plugins.append(StateRegistryPlugin())

    return plugins
