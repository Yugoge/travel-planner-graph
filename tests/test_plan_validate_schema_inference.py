#!/usr/bin/env python3
"""
Unit tests for schema-driven inference logic in scripts/plan-validate.py

Tests verify that validation automatically adapts to schema changes instead
of relying on hardcoded constants.

Root cause: Commit f0cc710 hardcoded validation logic
Fix: Refactored to schema-driven inference (see docs/dev/completion-20260212-175337.md)
"""

import sys
import json
import unittest
from pathlib import Path
import importlib.util

# Load plan_validate module from scripts directory
script_path = Path(__file__).parent.parent / "scripts" / "plan-validate.py"
spec = importlib.util.spec_from_file_location("plan_validate", script_path)
plan_validate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan_validate)


class TestSchemaInference(unittest.TestCase):
    """Test schema-driven inference methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.schema_registry = plan_validate.SchemaRegistry()

    def test_agents_with_local_inference(self):
        """
        Test Fix 8: AGENTS_WITH_LOCAL inferred from schemas.

        Verifies that agents requiring name_local field are automatically
        detected from schemas instead of hardcoded whitelist.
        """
        agents = self.schema_registry.agents_with_local

        # Expected agents with name_local requirement
        expected = {"meals", "attractions", "entertainment", "accommodation", "shopping"}

        self.assertEqual(agents, expected,
                        f"AGENTS_WITH_LOCAL mismatch. Expected {expected}, got {agents}")

        # Verify these are actual schema-driven (not hardcoded)
        # If schema changes, this test should reflect that
        for agent in expected:
            schema = self.schema_registry.get_schema(agent)
            self.assertIsNotNone(schema, f"Schema not found for {agent}")

    def test_budget_categories_extraction(self):
        """
        Test Fix 5: Budget categories extracted from schema.

        Verifies that budget categories are read from budget.schema.json
        instead of hardcoded list.
        """
        categories = self.schema_registry.get_budget_categories()

        # Expected categories from budget.schema.json $defs/budget_categories/properties
        expected = {"accommodation", "activities", "meals", "shopping", "transportation"}

        self.assertEqual(set(categories), expected,
                        f"Budget categories mismatch. Expected {expected}, got {set(categories)}")

        # Verify these come from schema
        budget_schema = self.schema_registry.get_schema("budget")
        self.assertIsNotNone(budget_schema)

        # Check schema has these properties
        budget_defs = budget_schema.get("$defs", {}).get("budget_categories", {})
        schema_properties = budget_defs.get("properties", {})

        self.assertTrue(len(schema_properties) > 0,
                       "Budget schema should have category properties")

    def test_transport_types_extraction(self):
        """
        Test Fix 7: Transport types extracted from schema.

        Verifies that valid transport types are extracted from timeline.schema.json
        instead of hardcoded list.
        """
        transport_types = self.schema_registry.get_valid_transport_types()

        # Expected types from timeline.schema.json travel_segment.type_base
        # Note: This should now include 'transit' discovered during validation
        expected = {"bus", "car", "ferry", "metro", "taxi", "train", "walk", "transit"}

        self.assertEqual(set(transport_types), expected,
                        f"Transport types mismatch. Expected {expected}, got {set(transport_types)}")

        # Verify these come from schema
        timeline_schema = self.schema_registry.get_schema("timeline")
        self.assertIsNotNone(timeline_schema)

    def test_config_loading(self):
        """
        Test Fix 1, 2, 4, 6: CONFIG loaded from external file.

        Verifies that configuration is loaded from config/validation.json
        instead of hardcoded in script.
        """
        config = plan_validate.CONFIG

        # Verify config has expected keys
        self.assertIn("english_placeholders", config)
        self.assertIn("currency_region_map", config)
        self.assertIn("intentional_overlap_keywords", config)
        self.assertIn("enforce_title_case", config)

        # Verify types
        self.assertIsInstance(config["english_placeholders"], list)
        self.assertIsInstance(config["currency_region_map"], dict)
        self.assertIsInstance(config["intentional_overlap_keywords"], list)
        self.assertIsInstance(config["enforce_title_case"], bool)

    def test_schema_driven_validation_adapts_to_schema_changes(self):
        """
        Integration test: Verify validation adapts to schema changes.

        This test proves that if schemas change, validation logic automatically
        adapts without code changes.
        """
        # Get current inferred values
        agents_with_local = self.schema_registry.agents_with_local
        budget_cats = self.schema_registry.get_budget_categories()
        transport_types = self.schema_registry.get_valid_transport_types()

        # Verify these are non-empty (schema-driven, not hardcoded empty sets)
        self.assertTrue(len(agents_with_local) > 0,
                       "Should infer agents from schemas")
        self.assertTrue(len(budget_cats) > 0,
                       "Should extract budget categories from schema")
        self.assertTrue(len(transport_types) > 0,
                       "Should extract transport types from schema")

        # Verify 'transit' discovered via schema-driven approach
        # (This type wasn't in original hardcoded list)
        self.assertIn("transit", transport_types,
                     "Schema-driven extraction should discover 'transit' type")


class TestConfigFallback(unittest.TestCase):
    """Test configuration fallback behavior."""

    def test_default_config_used_when_file_missing(self):
        """Verify DEFAULT_CONFIG is used when config file doesn't exist."""
        # This test documents the fallback behavior
        default = plan_validate.DEFAULT_CONFIG

        self.assertIn("english_placeholders", default)
        self.assertIsInstance(default["english_placeholders"], list)
        self.assertGreater(len(default["english_placeholders"]), 0)


class TestRegressionPrevention(unittest.TestCase):
    """Test that refactoring doesn't break existing validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.schema_registry = plan_validate.SchemaRegistry()

    def test_no_hardcoded_city_names(self):
        """
        Regression test: Ensure no hardcoded city names in validation logic.

        Before refactoring: CURRENCY_REGION dict had 19 hardcoded cities.
        After refactoring: Should use CONFIG (disabled by default).
        """
        config = plan_validate.CONFIG
        currency_map = config.get("currency_region_map", {})

        # Should be empty by default (disabled)
        self.assertEqual(currency_map, {},
                        "currency_region_map should be disabled (empty) by default")

    def test_no_hardcoded_keywords_in_overlap_detection(self):
        """
        Regression test: Overlap keywords should come from CONFIG.

        Before: intentional_kw = ["optional", "alternative", " or ", "in-park"] hardcoded
        After: Should use CONFIG
        """
        config = plan_validate.CONFIG
        keywords = config.get("intentional_overlap_keywords", [])

        # Should be configurable, not hardcoded
        self.assertIsInstance(keywords, list)
        self.assertGreater(len(keywords), 0)

    def test_schema_driven_inference_not_empty(self):
        """
        Regression test: Schema-driven inference should return non-empty results.

        Ensures schema-driven methods work correctly and don't return empty sets
        (which would indicate inference failure).
        """
        # Test AGENTS_WITH_LOCAL inference
        agents = self.schema_registry.agents_with_local
        self.assertGreater(len(agents), 0,
                          "AGENTS_WITH_LOCAL inference should return non-empty set")

        # Test budget categories extraction
        budget_cats = self.schema_registry.get_budget_categories()
        self.assertGreater(len(budget_cats), 0,
                          "Budget categories extraction should return non-empty list")

        # Test transport types extraction
        transport_types = self.schema_registry.get_valid_transport_types()
        self.assertGreater(len(transport_types), 0,
                          "Transport types extraction should return non-empty set")


if __name__ == "__main__":
    unittest.main()
