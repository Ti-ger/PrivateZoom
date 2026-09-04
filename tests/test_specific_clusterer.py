import sys
import types
import unittest

import pandas as pd


# The mask tests do not exercise graph construction. Keep this regression test
# runnable in the lightweight test environment where NetworkX is not installed.
sys.modules.setdefault("networkx", types.ModuleType("networkx"))
sys.modules.setdefault("pm4py", types.ModuleType("pm4py"))

from src.analysis.privacy import max_zoom
from src.clustering.instance_clusterer import InstanceClusterer
from src.clustering.resource_clusterer import ResourceClusterer
from src.clustering.specific_clusterer import build_mask


class BuildMaskTests(unittest.TestCase):
    def test_html_integer_string_matches_float_xes_value(self):
        df = pd.DataFrame({"Costs": [50.0, 400.0, 100.0, 400.0]})

        self.assertEqual(
            build_mask(df, "Costs", "400"),
            [False, True, False, True],
        )

    def test_string_attributes_remain_exact(self):
        df = pd.DataFrame({"Costs": ["0400", "400", "400.0"]})

        self.assertEqual(
            build_mask(df, "Costs", "400"),
            [False, True, False],
        )

    def test_mixed_column_preserves_numeric_and_literal_filters(self):
        df = pd.DataFrame({"Costs": [400.0, "*", "unknown", None]})

        for value, expected in [
            ("400", [True, False, False, False]),
            ("*", [False, True, False, False]),
            ("unknown", [False, False, True, False]),
            ("missing", [False, False, False, False]),
        ]:
            with self.subTest(filter=value):
                self.assertEqual(build_mask(df, "Costs", value), expected)

    def test_abstracted_filter_reveals_matching_resources(self):
        df = pd.DataFrame({
            "Resource": ["Mike", "Sue"],
            "Costs": [400.0, "*"],
        })
        max_zoom.init_max_zoom_df(df)
        clusterer = ResourceClusterer("Resource")
        clusterer.set_abstraction("Resource_abstracted")
        clusterer.set_mask([True] * len(df))

        abstraction = clusterer.abstractions["Resource_not_abstracted"]
        abstraction.set_mask_source_column("Costs")
        abstraction.set_mask_filter_attribute("*")
        abstraction.set_mask(build_mask(df, "Costs", "*"))
        clusterer.add_specific_abstraction(abstraction)

        result = clusterer.apply_abstraction(df.copy())

        self.assertEqual(result["Resource"].tolist(), ["*", "Sue"])

    def test_missing_filter_column_returns_an_empty_match(self):
        df = pd.DataFrame({"Resource": ["Mike", "Sue"]})

        self.assertEqual(
            build_mask(df, "Costs", "400"),
            [False, False],
        )

    def test_numeric_filter_reveals_matching_resources(self):
        df = pd.DataFrame({
            "Resource": ["Mike", "Pete", "Sue"],
            "Costs": [400.0, 100.0, 400.0],
        })
        max_zoom.init_max_zoom_df(df)

        resource_clusterer = ResourceClusterer("Resource")
        resource_clusterer.set_abstraction("Resource_abstracted")
        resource_clusterer.set_mask([True] * len(df))

        specific_abstraction = resource_clusterer.abstractions[
            "Resource_not_abstracted"
        ]
        specific_abstraction.set_mask_source_column("Costs")
        specific_abstraction.set_mask_filter_attribute("400")
        specific_abstraction.set_mask(build_mask(df, "Costs", "400"))
        resource_clusterer.add_specific_abstraction(specific_abstraction)

        result = resource_clusterer.apply_abstraction(df.copy())

        self.assertEqual(result["Resource"].tolist(), ["Mike", "*", "Sue"])


if __name__ == "__main__":
    unittest.main()
