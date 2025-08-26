import pytest

# test_7_external_search.py
def test_linkup_search_no_api_key():
    """Test that Linkup search fails without API key"""
    from src.external_enrichment import ExternalTestEnrichment
    
    enricher = ExternalTestEnrichment()
    with pytest.raises(EnvironmentError, match="LINKUP_API_KEY not set"):
        enricher.search_test_patterns("mobile app testing best practices")

def test_linkup_search_timeout():
    """Test that search timeout is handled properly"""
    from src.external_enrichment import ExternalTestEnrichment
    from unittest.mock import patch
    
    enricher = ExternalTestEnrichment(api_key="test_key", timeout=1)
    with patch('requests.post', side_effect=TimeoutError):
        with pytest.raises(TimeoutError, match="External search timed out after 1 seconds"):
            enricher.search_test_patterns("test query")

def test_mistral_completion_invalid_prompt():
    """Test that Mistral AI rejects invalid prompts"""
    from src.llm_integration import MistralTestEnhancer
    
    enhancer = MistralTestEnhancer()
    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        enhancer.enhance_test_case("")