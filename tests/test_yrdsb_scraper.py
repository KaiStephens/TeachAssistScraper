import unittest
import sys
import os

# Adjust sys.path to include the project root directory
# This allows importing yrdsb_scraper from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from yrdsb_scraper import parse_percentage, normalize_bgcolor # Removed extract_mark_text as it's not part of this subtask

class TestScraperHelpers(unittest.TestCase):
    def test_valid_percentages(self):
        self.assertEqual(parse_percentage("75%"), 75.0)
        self.assertEqual(parse_percentage("88.5 %"), 88.5)
        self.assertEqual(parse_percentage(" 92.3% "), 92.3)
        self.assertEqual(parse_percentage("100%"), 100.0)
        self.assertEqual(parse_percentage("0%"), 0.0)
        self.assertEqual(parse_percentage("Mark: 95%"), 95.0) # Test with leading text

    def test_invalid_percentages(self):
        self.assertIsNone(parse_percentage("No Mark"))
        self.assertIsNone(parse_percentage("N/A"))
        self.assertIsNone(parse_percentage(""))
        self.assertIsNone(parse_percentage("abc"))
        self.assertIsNone(parse_percentage("Level 4"))
        self.assertIsNone(parse_percentage("100")) # No percent sign
        self.assertIsNone(parse_percentage("%")) # Only percent sign

    def test_various_formats_bgcolor(self):
        self.assertEqual(normalize_bgcolor("#FFFFFF"), "ffffff")
        self.assertEqual(normalize_bgcolor("ffffff"), "ffffff")
        self.assertEqual(normalize_bgcolor("#ABC"), "abc")
        self.assertEqual(normalize_bgcolor("abc"), "abc")
        self.assertEqual(normalize_bgcolor("FFD700"), "ffd700")
        self.assertEqual(normalize_bgcolor("#ffd700"), "ffd700")

    def test_empty_and_none_bgcolor(self):
        self.assertEqual(normalize_bgcolor(""), "")
        self.assertEqual(normalize_bgcolor(None), "")

if __name__ == '__main__':
    unittest.main()
