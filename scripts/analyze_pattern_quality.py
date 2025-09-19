#!/usr/bin/env python3
"""
Quality Analysis of External Patterns

This script analyzes the actual quality and value of the "external patterns"
being discovered to determine if they're meaningful or just web scraping.
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, 'src')

from external_enrichment import ExternalTestEnrichment

def analyze_pattern_quality():
    print("=== EXTERNAL PATTERN QUALITY ANALYSIS ===")

    enrichment = ExternalTestEnrichment()

    # Test component
    component = {
        'component_type': 'button',
        'component_id': 'login_btn',
        'properties': {'text': 'Login', 'enabled': True}
    }

    # Get patterns
    patterns = enrichment.discover_patterns_for_component(component)
    print(f"\nFound {len(patterns)} patterns for analysis")

    # Analyze first 5 patterns in detail
    for i, pattern in enumerate(patterns[:5]):
        print(f"\n{'='*60}")
        print(f"PATTERN {i+1} ANALYSIS")
        print(f"{'='*60}")

        print(f"Title: {pattern.get('title', 'No title')}")
        print(f"Source: {pattern.get('source', 'Unknown')}")
        print(f"URL: {pattern.get('external_url', 'No URL')}")
        print(f"Quality Score: {pattern.get('confidence_score', 0)}")
        print(f"Category: {pattern.get('category', 'Unknown')}")

        # Analyze description
        description = pattern.get('description', '')
        print(f"\nDescription Length: {len(description)} chars")
        print(f"Description: {description[:200]}...")

        # Analyze test template
        test_template = pattern.get('test_template', '')
        print(f"\nTest Template Length: {len(test_template)} chars")
        print(f"Test Template:")
        print(test_template)

        # Check for meaningful content
        print(f"\nQUALITY INDICATORS:")
        print(f"- Has meaningful description: {len(description) > 50}")
        print(f"- Has test code: {len(test_template) > 0}")
        print(f"- Contains selenium/automation code: {'selenium' in test_template.lower() or 'driver' in test_template.lower()}")
        print(f"- Contains assertions: {'assert' in test_template.lower()}")
        print(f"- Component-specific: {component['component_id'] in test_template}")

        # Check metadata
        metadata = pattern.get('metadata', {})
        print(f"- Has framework info: {bool(metadata.get('framework'))}")
        print(f"- Has author info: {bool(metadata.get('author'))}")
        print(f"- Has tags: {bool(metadata.get('tags'))}")

def analyze_enriched_tests():
    print(f"\n{'='*60}")
    print("ENRICHED TEST SUITE ANALYSIS")
    print(f"{'='*60}")

    enrichment = ExternalTestEnrichment()

    component = {
        'component_type': 'button',
        'component_id': 'login_btn',
        'properties': {'text': 'Login'}
    }

    # Base test suite
    base_tests = [
        {
            'name': 'test_button_click',
            'description': 'Test basic button click',
            'type': 'interaction'
        }
    ]

    # Enrich tests
    enriched_tests = enrichment.enrich_test_suite(base_tests, component)

    print(f"Base tests: {len(base_tests)}")
    print(f"Enriched tests: {len(enriched_tests)}")
    print(f"External tests added: {len(enriched_tests) - len(base_tests)}")

    # Analyze external tests
    external_tests = []
    for test in enriched_tests:
        if 'external' in test.get('source', '').lower():
            external_tests.append(test)

    print(f"\nExternal tests found: {len(external_tests)}")

    # Sample external test analysis
    if external_tests:
        sample_test = external_tests[0]
        print(f"\nSAMPLE EXTERNAL TEST ANALYSIS:")
        print(f"Name: {sample_test.get('name', 'Unknown')}")
        print(f"Description: {sample_test.get('description', 'No description')}")
        print(f"Category: {sample_test.get('category', 'Unknown')}")
        print(f"Priority: {sample_test.get('priority', 'Unknown')}")
        print(f"Source: {sample_test.get('source', 'Unknown')}")

        test_code = sample_test.get('test_code', '')
        print(f"\nTest Code ({len(test_code)} chars):")
        print(test_code)

        # Quality assessment
        print(f"\nQUALITY ASSESSMENT:")
        print(f"- Runnable test code: {'def test_' in test_code}")
        print(f"- Uses WebDriver: {'driver' in test_code}")
        print(f"- Has assertions: {'assert' in test_code}")
        print(f"- Component-specific: {component['component_id'] in test_code}")
        print(f"- Follows conventions: {test_code.count('def ') == 1}")

def test_value_proposition():
    print(f"\n{'='*60}")
    print("VALUE PROPOSITION ANALYSIS")
    print(f"{'='*60}")

    enrichment = ExternalTestEnrichment()

    # Test multiple component types
    components = [
        {'component_type': 'button', 'component_id': 'submit_btn'},
        {'component_type': 'list', 'component_id': 'game_list'},
        {'component_type': 'api_endpoint', 'component_id': 'scores_api'},
    ]

    total_patterns = 0
    for comp in components:
        patterns = enrichment.discover_patterns_for_component(comp)
        total_patterns += len(patterns)
        print(f"{comp['component_type']}: {len(patterns)} patterns")

    print(f"\nTotal patterns across components: {total_patterns}")

    # Check for duplication
    all_pattern_titles = set()
    unique_patterns = 0

    for comp in components:
        patterns = enrichment.discover_patterns_for_component(comp)
        for pattern in patterns:
            title = pattern.get('title', '')
            if title not in all_pattern_titles:
                all_pattern_titles.add(title)
                unique_patterns += 1

    print(f"Unique patterns: {unique_patterns}")
    print(f"Duplication rate: {((total_patterns - unique_patterns) / total_patterns * 100):.1f}%")

    # Test trending patterns
    trending = enrichment.get_trending_patterns()
    print(f"Trending patterns: {len(trending)}")

if __name__ == "__main__":
    analyze_pattern_quality()
    analyze_enriched_tests()
    test_value_proposition()