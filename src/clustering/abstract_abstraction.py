from abc import ABC
from collections import defaultdict
import numpy as np


class AbstractAbstraction(ABC):

    def __init__(self, source_col, target_col, abstraction_function, ranking=1):
        self.source_col = source_col
        self.target_col = target_col
        self.abstraction_function = abstraction_function
        self.ranking = ranking
        self.mask = None
        self.mask_source_col = None
        self.mask_filter_attribute = None
        self.l_div_map = defaultdict(set)

    def apply_abstraction(self, value):
        abstracted_value = self.abstraction_function(value)
        self.l_div_map[abstracted_value].add(value)
        return abstracted_value

    def set_mask(self, mask):
        self.mask =  mask

    def set_mask_source_column(self, mask_source_column):
        self.mask_source_col = mask_source_column

    def set_mask_filter_attribute(self, mask_filter_attribute):
        self.mask_filter_attribute = mask_filter_attribute

    def get_l_div_map(self):
        # JSON's default serializer is never called for dictionary keys.
        # Normalize NumPy scalars here, including numerical class boundaries.
        def native_scalar(value):
            return value.item() if isinstance(value, np.generic) else value

        return {
            native_scalar(key): [native_scalar(value) for value in values]
            for key, values in self.l_div_map.items()
        }
