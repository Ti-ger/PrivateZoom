"""Regression tests for privacy enforcement."""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
from pm4py.objects.log.obj import Event, EventLog, Trace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.privacy import privacy_checker
from src.analysis.privacy import l_diversity


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


class LDiversityLoaderTests(unittest.TestCase):
    def test_loader_reads_the_supplied_mapping_path(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            requested_path = directory / "requested.json"
            global_path = directory / "global.json"
            requested_path.write_text(
                '{"activity": {"*": ["a", "b"]}}', encoding="utf-8"
            )
            global_path.write_text('{"wrong": true}', encoding="utf-8")

            with patch.object(l_diversity, "L_DIVERSITY_PATH", global_path):
                result = l_diversity.load_l_diversity_map(requested_path)

        self.assertEqual(result, {"activity": {"*": ["a", "b"]}})


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

    def test_edge_deletion_returns_the_filtered_log(self):
        first = Trace(
            [Event({"concept:name": "a"}), Event({"concept:name": "b"})],
            attributes={"concept:name": "case-1"},
        )
        second = Trace(
            [Event({"concept:name": "a"}), Event({"concept:name": "c"})],
            attributes={"concept:name": "case-2"},
        )
        log = EventLog([first, second])
        edge_hash = (hash(first[0]), hash(first[1]))

        with patch.object(privacy_checker.pm4py, "write_xes"):
            deleted, filtered = privacy_checker.delete_edge_by_hash(
                "log.xes", [edge_hash], log
            )

        self.assertEqual(deleted, ["case-1"])
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].attributes["concept:name"], "case-2")

    def test_follow_event_l_diversity_receives_path_and_current_log(self):
        frame = pd.DataFrame(
            {
                "case:concept:name": ["case-1"],
                "concept:name": ["a"],
            }
        )
        current_log = object()

        with (
            patch.object(
                privacy_checker, "load_event_log", return_value=current_log
            ),
            patch.object(privacy_checker, "check_empty_log", return_value=False),
            patch.object(
                privacy_checker,
                "get_k_anonymity",
                return_value=({}, {}, {}),
            ),
            patch.object(
                privacy_checker, "get_l_diversity", return_value={}
            ) as get_l_diversity,
            patch.object(
                privacy_checker,
                "delete_event_by_hash",
                return_value=([], current_log),
            ),
            patch.object(privacy_checker.max_zoom, "export_max_zoom_df"),
        ):
            privacy_checker.delete_trace(
                frame,
                "log.xes",
                l_div=2,
                follow_event_l_div=True,
            )

        get_l_diversity.assert_called_once_with("log.xes", current_log)

    def test_trace_deletion_returns_the_filtered_log(self):
        first = Trace(
            [Event({"concept:name": "a"})],
            attributes={"concept:name": "case-1"},
        )
        second = Trace(
            [Event({"concept:name": "b"})],
            attributes={"concept:name": "case-2"},
        )
        log = EventLog([first, second])
        trace_hash = hash(privacy_checker.trace_to_tuple(first))

        with patch.object(privacy_checker.pm4py, "write_xes"):
            deleted, filtered = privacy_checker.delete_trace_by_hash(
                "log.xes", [trace_hash], log
            )

        self.assertEqual(deleted, ["case-1"])
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].attributes["concept:name"], "case-2")


if __name__ == "__main__":
    unittest.main()
