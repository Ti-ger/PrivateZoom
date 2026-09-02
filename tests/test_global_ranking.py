import sys
import unittest
from types import SimpleNamespace

import pandas as pd


captured = {}


def discover_footprints(df):
    captured["activities"] = df["concept:name"].tolist()
    return {
        "start_activities": {"register request"},
        "end_activities": {"pay compensation"},
        "activities": {
            "register request",
            "examine thoroughly",
            "pay compensation",
        },
    }


sys.modules["pm4py"] = SimpleNamespace(discover_footprints=discover_footprints)

from src.algo.global_ranking import global_ranking_method_df_relativetime


class GlobalRankingTests(unittest.TestCase):
    def test_custom_activity_column_is_used_for_footprints(self):
        frame = pd.DataFrame({
            "concept:name": ["legacy", "legacy", "legacy"],
            "Activity": [
                "pay compensation",
                "examine thoroughly",
                "register request",
            ],
            "time:relative:seconds": [30, 10, 0],
        })

        actual = global_ranking_method_df_relativetime(
            frame,
            act_col="Activity",
        )

        self.assertEqual(captured["activities"], frame["Activity"].tolist())
        self.assertEqual(actual, {
            1: "register request",
            2: "examine thoroughly",
            3: "pay compensation",
        })


if __name__ == "__main__":
    unittest.main()
