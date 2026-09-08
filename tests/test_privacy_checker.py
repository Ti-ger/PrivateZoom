"""Regression tests for privacy enforcement."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import pandas as pd

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


class PrivacyDeletionTests(unittest.TestCase):
    def test_trace_deletion_keeps_the_helper_result_as_a_pair(self):
        frame = pd.DataFrame(
            {
                "case:concept:name": ["case-1", "case-2"],
                "concept:name": ["a", "b"],
            }
        )
        initial_log = object()
        filtered_log = object()

        with (
            patch.object(
                privacy_checker, "load_event_log", return_value=initial_log
            ),
            patch.object(privacy_checker, "check_empty_log", return_value=False),
            patch.object(
                privacy_checker,
                "get_k_anonymity",
                side_effect=[({"rare": 1}, {}, {}), ({"common": 2}, {}, {})],
            ),
            patch.object(
                privacy_checker,
                "delete_trace_by_hash",
                side_effect=[(["case-1"], filtered_log), ([], filtered_log)],
            ),
            patch.object(privacy_checker.max_zoom, "export_max_zoom_df"),
        ):
            result = privacy_checker.delete_trace(
                frame, "log.xes", min_k_trace=2
            )

        self.assertEqual(result["case:concept:name"].tolist(), ["case-2"])


if __name__ == "__main__":
    unittest.main()
