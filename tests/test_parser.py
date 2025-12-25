#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOLDEN TESTS for Parser
Verify parser works correctly on known fixtures
"""

import sys
import os
import subprocess
import unittest
from pathlib import Path

# Add tools/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from smart_parser import parse_overview, parse_index
from parser_models import ParsedResult


class TestParserGolden(unittest.TestCase):
    """Golden tests using baocao_full.txt fixture"""

    @classmethod
    def setUpClass(cls):
        """Load test fixture once"""
        cls.fixture_path = Path(__file__).parent.parent / "reports" / "txt" / "baocao_full.txt"
        if not cls.fixture_path.exists():
            raise FileNotFoundError(f"Fixture not found: {cls.fixture_path}")

        with open(cls.fixture_path, 'r', encoding='utf-8') as f:
            cls.fixture_content = f.read()

    def test_parse_overview_success(self):
        """Test overview parsing succeeds"""
        result = parse_overview(self.fixture_content)

        self.assertIsInstance(result, ParsedResult)
        self.assertTrue(result.is_success(), "Overview should parse successfully")
        self.assertIsNotNone(result.data, "Should have parsed data")
        self.assertEqual(result.data.key, "overview")
        self.assertIsNotNone(result.data.sections, "Should have sections")
        self.assertGreater(len(result.data.sections), 0, "Overview should have at least 1 section")

    def test_parse_all_16_indices(self):
        """Test all 16 indices can be parsed"""
        indices = [
            ('VNINDEX', 'vnindex'),
            ('VN30', 'vn30'),
            ('VN100', 'vn100'),
            ('VNMIDCAP', 'vnmidcap'),
            ('VNREAL', 'vnreal'),
            ('VNIT', 'vnit'),
            ('VNHEAL', 'vnheal'),
            ('VNFIN', 'vnfin'),
            ('VNENE', 'vnene'),
            ('VNCONS', 'vncons'),
            ('VNMAT', 'vnmat'),
            ('VNCOND', 'vncond'),
            ('VNSML', 'vnsml'),
            ('VNFINSELECT', 'vnfinselect'),
            ('VNDIAMOND', 'vndiamond')
        ]

        for index_name, index_code in indices:
            with self.subTest(index=index_name):
                result = parse_index(self.fixture_content, index_name, index_code)
                self.assertTrue(result.is_success(),
                              f"{index_name} should parse successfully. Error: {result.get_error_summary()}")
                self.assertIsNotNone(result.data, f"{index_name} should have data")
                self.assertEqual(result.data.key, index_code)

    def test_output_js_valid(self):
        """Test generated JS passes node --check"""
        # Generate output file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            output_file = f.name

        try:
            # Run auto_parse.py
            auto_parse_path = Path(__file__).parent.parent / "tools" / "auto_parse.py"
            result = subprocess.run(
                [sys.executable, str(auto_parse_path),
                 str(self.fixture_path), output_file],
                capture_output=True,
                text=True
            )

            self.assertEqual(result.returncode, 0, "auto_parse.py should exit successfully")

            # Verify JS syntax
            node_result = subprocess.run(
                ['node', '--check', output_file],
                capture_output=True,
                text=True
            )

            self.assertEqual(node_result.returncode, 0,
                           f"Generated JS should be valid. node error: {node_result.stderr}")
        finally:
            # Cleanup
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_structured_errors_on_invalid_input(self):
        """Test structured error handling for invalid input"""
        result = parse_index("This is not valid content", "INVALID", "invalid")

        self.assertFalse(result.is_success(), "Should fail for invalid content")
        self.assertIsNotNone(result.error, "Should have error info")
        self.assertIn(result.error.error_type,
                     ["IndexHeaderNotFound", "NoSectionsFound", "InvalidBoundaries"],
                     "Should have specific error type")

    def test_output_has_all_keys(self):
        """Test generated output contains all expected keys"""
        import tempfile
        import json

        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            output_file = f.name

        try:
            # Generate output
            auto_parse_path = Path(__file__).parent.parent / "tools" / "auto_parse.py"
            subprocess.run(
                [sys.executable, str(auto_parse_path),
                 str(self.fixture_path), output_file],
                capture_output=True
            )

            # Read and check content
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for all expected keys
            expected_keys = ['overview', 'vnindex', 'vn30', 'vn100', 'vnmidcap',
                            'vnreal', 'vnit', 'vnheal', 'vnfin', 'vnene',
                            'vncons', 'vnmat', 'vncond', 'vnsml', 'vnfinselect', 'vndiamond']

            for key in expected_keys:
                self.assertIn(f'{key}:', content,
                            f"Output should contain {key}")

        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestParserEdgeCases(unittest.TestCase):
    """Edge case tests not requiring fixture"""

    def test_empty_content(self):
        """Test parsing empty content"""
        result = parse_index("", "TEST", "test")
        self.assertFalse(result.is_success())

    def test_content_with_backticks(self):
        """Test content with backticks is handled safely"""
        from smart_parser import js_str

        # The key safety feature: js_str returns a double-quoted JSON string
        # NOT a template literal, so backticks and ${} are safe
        test_string = "Test `backtick` and ${interpolation}"
        escaped = js_str(test_string)

        # Should be double-quoted JSON, not backtick-wrapped template literal
        self.assertTrue(escaped.startswith('"'), "Should start with double quote")
        self.assertTrue(escaped.endswith('"'), "Should end with double quote")
        self.assertNotIn("`", escaped[0], "First char should be quote, not backtick")

        # Should be valid JSON that can be decoded
        import json
        decoded = json.loads(escaped)
        self.assertEqual(decoded, test_string, "Should preserve original content")

        # Verify content with special characters survives roundtrip
        dangerous_strings = [
            "Text with `backticks`",
            "Text with ${interpolation}",
            "Text with \\backslash\\",
            "Text with 'single' and \"double\" quotes",
            "Text with\nnewlines\tand\ttabs"
        ]

        for s in dangerous_strings:
            with self.subTest(string=s):
                enc = js_str(s)
                dec = json.loads(enc)
                self.assertEqual(dec, s, f"Roundtrip failed for: {s}")

    def test_content_with_special_chars(self):
        """Test special characters are handled"""
        from smart_parser import js_str, normalize_text

        # Test normalization
        weird_text = "Text\u2028with\u2029weird\u000cwhitespace"
        normalized = normalize_text(weird_text)

        self.assertNotIn('\u2028', normalized)
        self.assertNotIn('\u2029', normalized)
        self.assertIn('\n', normalized)


def run_tests():
    """Run all tests and return exit code"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestParserGolden))
    suite.addTests(loader.loadTestsFromTestCase(TestParserEdgeCases))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
