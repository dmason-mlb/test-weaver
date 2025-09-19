#!/usr/bin/env python3
"""
Examine actual pipeline output in detail
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, 'src')

def examine_pipeline_output():
    """Examine what the pipeline actually generates."""
    print("=== EXAMINING ACTUAL PIPELINE OUTPUT ===")

    try:
        from pipeline import TestGenerationPipeline

        pipeline = TestGenerationPipeline(verbose=False)

        # Simple UI schema
        ui_schema = {
            'components': [
                {
                    'component_id': 'login_btn',
                    'component_type': 'button',
                    'properties': {
                        'text': 'Login',
                        'enabled': True
                    }
                }
            ]
        }

        print("Testing generate_tests_for_ui...")
        results = pipeline.generate_tests_for_ui(ui_schema)

        print(f"Result type: {type(results)}")
        print(f"Result keys: {list(results.keys()) if isinstance(results, dict) else 'Not a dict'}")

        print(f"\nFull result:")
        print(json.dumps(results, indent=2)[:1000] + "..." if len(str(results)) > 1000 else json.dumps(results, indent=2))

        print(f"\n{'='*50}")
        print("Testing generate_all_test_scenarios...")

        all_scenarios = pipeline.generate_all_test_scenarios(ui_schema)
        print(f"All scenarios type: {type(all_scenarios)}")
        print(f"All scenarios length: {len(all_scenarios) if isinstance(all_scenarios, (list, dict)) else 'Not a list/dict'}")

        if isinstance(all_scenarios, list):
            print(f"First few scenarios:")
            for i, scenario in enumerate(all_scenarios[:3]):
                print(f"  Scenario {i+1}: {type(scenario)} - {str(scenario)[:100]}...")
        elif isinstance(all_scenarios, dict):
            print(f"Scenario keys: {list(all_scenarios.keys())}")
            for key, value in list(all_scenarios.items())[:3]:
                print(f"  {key}: {type(value)} - {len(value) if isinstance(value, (list, dict)) else str(value)[:50]}")

    except Exception as e:
        print(f"Examination failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    examine_pipeline_output()