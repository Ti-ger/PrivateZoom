"""Regression checks for cached imports and optimized abstraction execution."""
import copy
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from pandas.testing import assert_frame_equal
from src.analysis.privacy import max_zoom
from src.clustering.resource_clusterer import ResourceClusterer, ResourceAbstraction
from src.clustering.specific_clusterer import build_mask
from src.utils import data_importing
from src.utils.data_processing import simplifyLog
from src.analysis import attribute_extractor


class PerformanceRegressionTests(unittest.TestCase):
    def test_concept_name_is_hidden_only_when_activity_is_available(self):
        mapping = {'Activity': 'activity', 'concept:name': 'activity', 'Costs': 'numerical'}
        self.assertEqual(attribute_extractor.get_ui_attribute_mapping(mapping), {
            'Activity': 'activity', 'Costs': 'numerical',
        })
        self.assertEqual(
            attribute_extractor.get_ui_attribute_mapping({'concept:name': 'activity'}),
            {'concept:name': 'activity'},
        )

    def test_shared_parse_preserves_attribute_schema(self):
        path = str(Path(__file__).resolve().parents[1] / 'data/evaluation_data/runningexample.xes')
        with patch.object(attribute_extractor, 'write_to_file'):
            attribute_extractor.reset_attribute_mapping()
            attribute_extractor.extract_attributes(path)
            attribute_extractor.extract_attribute_type_mapping()
            expected = attribute_extractor.event_attribute_type_mapping.copy()
            attribute_extractor.reset_attribute_mapping()
            log = data_importing.load_xes_event_log(path)
            attribute_extractor.extract_attributes(path, log=log)
            converted = data_importing.event_log_to_dataframe(log)
            attribute_extractor.extract_attribute_type_mapping()
            self.assertEqual(attribute_extractor.event_attribute_type_mapping, expected)
            assert_frame_equal(converted, data_importing.load_event_log_from_tempfile(path))

    def test_cached_log_is_isolated_and_reloaded_when_file_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'log.xes'
            path.write_text('first')
            original = pd.DataFrame({'value': [1, 2]})
            with patch.object(data_importing, 'load_event_log_from_tempfile',
                              return_value=original) as load:
                first = data_importing.load_cached_event_log(str(path))
                first.loc[0, 'value'] = 99
                assert_frame_equal(data_importing.load_cached_event_log(str(path)), original)
                self.assertEqual(load.call_count, 1)
                path.write_text('second log')
                data_importing.load_cached_event_log(str(path))
                self.assertEqual(load.call_count, 2)
                stat = path.stat()
                os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
                data_importing.load_cached_event_log(str(path))
                self.assertEqual(load.call_count, 3)

    def test_no_variant_discovery_without_variant_filter(self):
        frame = pd.DataFrame({'concept:name': ['a']})
        with patch('src.utils.data_processing.pm4py.get_variants') as discover:
            assert_frame_equal(simplifyLog(frame), frame)
            discover.assert_not_called()

    def test_overlapping_zooms_preserve_priority_and_privacy_history(self):
        frame = pd.DataFrame({'Resource': ['Mike', 'Pete', 'Sue', 'Ann'],
                              'Costs': [400, 100, 400, 100],
                              'Group': ['all'] * 4}, index=[10, 20, 30, 40])
        max_zoom.init_max_zoom_df(frame)
        history = max_zoom.get_max_zoom_df()
        history.loc[10, 'rank_Resource'] = 200
        history.loc[10, 'Resource'] = 'previous'
        clusterer = ResourceClusterer('Resource')
        clusterer.set_mask([True] * len(frame))
        low = ResourceAbstraction('Resource', 'Resource', lambda value: 'group', 50)
        low.set_mask_source_column('Group')
        low.set_mask_filter_attribute('all')
        high = copy.deepcopy(clusterer.abstractions['Resource_not_abstracted'])
        high.set_mask_source_column('Costs')
        high.set_mask_filter_attribute('400')
        for abstraction in (low, high):
            abstraction.set_mask(build_mask(frame, abstraction.mask_source_col,
                                           abstraction.mask_filter_attribute))
            clusterer.add_specific_abstraction(abstraction)
        clusterer.calculate_masks()
        result = clusterer.apply_abstraction(frame.copy())
        self.assertEqual(result['Resource'].tolist(), ['Mike', 'group', 'Sue', 'group'])
        self.assertEqual(history['Resource'].tolist(), ['previous', 'group', 'Sue', 'group'])
        self.assertEqual(history['rank_Resource'].tolist(), [200, 50, 100, 50])
        self.assertEqual(set(clusterer.get_l_div()['group']), {'Pete', 'Ann'})


if __name__ == '__main__':
    unittest.main()
