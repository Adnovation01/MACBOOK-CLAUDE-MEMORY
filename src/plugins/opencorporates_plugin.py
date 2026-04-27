import requests
from urllib.parse import quote
from typing import List
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin

class OpenCorporatesPlugin(BasePlugin):
    name = "opencorporates"
    requires_auth = False
    rate_limit_seconds = 3.0

    def search(self, keyword: str, location: str, max_leads: int) -> List[Lead]:
        leads = []
        city = location.split(',')[0].strip()
        state = location.split(',')[1].strip() if ',' in location else ''
        try:
            url = f"https://api.opencorporates.com/v0.4/companies/search?q={quote(keyword)}&jurisdiction_code=us_{state.lower()}&per_page={max_leads}"
            r = requests.get(url, timeout=15)
            data = r.json()
            for item in data.get('results', {}).get('companies', [])[:max_leads]:
                co = item.get('company', {})
                name = co.get('name', '')
                if name:
                    leads.append(Lead(
                        business_name=name,
                        address=co.get('registered_address_in_full', ''),
                        city=city, state=state,
                        sources=['opencorporates']
                    ))
        except Exception:
            pass
        return leads
