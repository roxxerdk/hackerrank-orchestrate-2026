import sys
import os
import unittest
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional
from app.features.feature_utils import (
    clamp_ratio,
    is_in_dnd,
    detect_links,
    detect_urgency_keywords,
    get_time_bucket,
    is_weekend,
)
from app.features.routing_features import TemporalBucket

class TestFeatureUtils(unittest.TestCase):

    def test_clamp_ratio(self):
        self.assertEqual(clamp_ratio(5, 10), 0.5)
        self.assertEqual(clamp_ratio(15, 10), 1.0)
        self.assertEqual(clamp_ratio(-1, 10), 0.0)
        self.assertEqual(clamp_ratio(5, 0), 0.0)

    def test_is_in_dnd(self):
        # Overnight window test (22:00 to 07:00)
        dnd_window = "22:00-07:00"
        self.assertTrue(is_in_dnd(datetime(2026, 8, 1, 23, 0), dnd_window))
        self.assertTrue(is_in_dnd(datetime(2026, 8, 1, 6, 30), dnd_window))
        self.assertFalse(is_in_dnd(datetime(2026, 8, 1, 12, 0), dnd_window))

        # Standard window test (09:00 to 17:00)
        dnd_window_day = "09:00-17:00"
        self.assertTrue(is_in_dnd(datetime(2026, 8, 1, 10, 0), dnd_window_day))
        self.assertFalse(is_in_dnd(datetime(2026, 8, 1, 8, 0), dnd_window_day))

        # Invalid window parsing
        self.assertFalse(is_in_dnd(datetime(2026, 8, 1, 12, 0), "invalid_window"))
        self.assertFalse(is_in_dnd(datetime(2026, 8, 1, 12, 0), ""))

    def test_detect_links(self):
        self.assertTrue(detect_links("Check this out: https://google.com"))
        self.assertTrue(detect_links("Visit http://test.org/path"))
        self.assertFalse(detect_links("No link here, just text."))
        self.assertFalse(detect_links(""))
        self.assertFalse(detect_links(None))

    def test_detect_urgency_keywords(self):
        self.assertTrue(detect_urgency_keywords("This is an URGENT request!"))
        self.assertTrue(detect_urgency_keywords("Action required before today."))
        self.assertFalse(detect_urgency_keywords("Normal update message."))
        self.assertFalse(detect_urgency_keywords("todaycare health clinic")) # Word boundaries validation
        self.assertFalse(detect_urgency_keywords(""))
        self.assertFalse(detect_urgency_keywords(None))

    def test_get_time_bucket(self):
        self.assertEqual(get_time_bucket(datetime(2026, 8, 1, 8, 0)), TemporalBucket.MORNING)
        self.assertEqual(get_time_bucket(datetime(2026, 8, 1, 14, 0)), TemporalBucket.AFTERNOON)
        self.assertEqual(get_time_bucket(datetime(2026, 8, 1, 18, 0)), TemporalBucket.EVENING)
        self.assertEqual(get_time_bucket(datetime(2026, 8, 1, 3, 0)), TemporalBucket.NIGHT)

    def test_is_weekend(self):
        # Saturday
        self.assertTrue(is_weekend(datetime(2026, 8, 1)))
        # Sunday
        self.assertTrue(is_weekend(datetime(2026, 8, 2)))
        # Monday
        self.assertFalse(is_weekend(datetime(2026, 8, 3)))

if __name__ == "__main__":
    unittest.main()
