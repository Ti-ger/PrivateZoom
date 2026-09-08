"""Regression tests for privacy enforcement."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.privacy import privacy_checker


class PrivacyMetricTests(unittest.TestCase):
    def test_combined_check_uses_event_threshold_for_event_counts(self):
        with (
            patch.object(privacy_checker, "load_event_log", return_value=object()),
            patch.object(
                privacy_checker,
                "get_k_anonymity",
                return_value=({"trace": 5}, {"edge": 4}, {"event": 2}),
            ),
        ):
            self.assertTrue(
                privacy_checker.check_metrics(
                    "log.xes", k_trace=2, k_event=2, k_edge=4
                )
            )

    def test_combined_check_uses_edge_threshold_for_edge_counts(self):
        with (
            patch.object(privacy_checker, "load_event_log", return_value=object()),
            patch.object(
                privacy_checker,
                "get_k_anonymity",
                return_value=({"trace": 5}, {"edge": 1}, {"event": 5}),
            ),
        ):
            self.assertFalse(
                privacy_checker.check_metrics(
                    "log.xes", k_trace=2, k_event=3, k_edge=2
                )
            )


if __name__ == "__main__":
    unittest.main()
