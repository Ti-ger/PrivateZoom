import json
import unittest

import numpy as np
import pandas as pd

from src.clustering.abstract_abstraction import AbstractAbstraction
from src.clustering.numerical_clusterer import NumericalAbstraction, _split_range


class AbstractionSerializationTests(unittest.TestCase):
    def test_integer_class_boundaries_can_be_written_as_json_keys(self):
        values = pd.Series([100, 200, 300, 400], dtype='int64')
        abstraction = NumericalAbstraction('Costs', 'Costs', _split_range(values, 2))
        for value in values:
            abstraction.apply_abstraction(value)

        encoded = json.dumps({'Costs': abstraction.get_l_div_map()})

        result = json.loads(encoded)['Costs']
        self.assertEqual({key: set(values) for key, values in result.items()}, {
            '200': {100.0, 200.0}, '400': {300.0, 400.0},
        })

    def test_numpy_scalar_keys_and_values_are_converted_without_rounding(self):
        abstraction = AbstractAbstraction('value', 'value', lambda value: value)
        abstraction.apply_abstraction(np.int64(2**60 + 1))
        abstraction.apply_abstraction(np.float32(1.5))

        result = json.loads(json.dumps(abstraction.get_l_div_map()))

        self.assertEqual(result[str(2**60 + 1)], [2**60 + 1])
        self.assertEqual(result['1.5'], [1.5])


if __name__ == '__main__':
    unittest.main()
