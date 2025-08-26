import os
import requests


class ExternalTestEnrichment:
    def __init__(self, api_key=None, timeout=30):
        self.api_key = api_key
        self.timeout = timeout
    
    def search_test_patterns(self, query):
        if not self.api_key and not os.getenv('LINKUP_API_KEY'):
            raise EnvironmentError("LINKUP_API_KEY not set")
        
        try:
            # This would normally make an actual API call
            response = requests.post(
                "https://api.linkup.com/search", 
                json={"query": query},
                timeout=self.timeout
            )
            return response.json()
        except (requests.Timeout, TimeoutError):
            raise TimeoutError(f"External search timed out after {self.timeout} seconds")