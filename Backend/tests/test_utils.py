import unittest
import math
import numpy as np
import sys
import os

# Ensure the Backend directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Assuming sanitize_value is defined in risk_assessment.py or a similar accessible place.
# For this test, we'll use the one from risk_assessment.
# If it's moved to a common utils, this import path should change.
from services.risk_assessment import sanitize_value
# If sanitize_value is also in suggestions_services and identical, this is fine.
# If they are different, tests might need to be specific or the function centralized.

class TestSanitizeValue(unittest.TestCase):

    def test_sanitize_plain_floats(self):
        self.assertIsNone(sanitize_value(float('inf')))
        self.assertIsNone(sanitize_value(float('-inf')))
        self.assertIsNone(sanitize_value(math.nan))
        self.assertEqual(sanitize_value(10.0), 10.0)
        self.assertIsNone(sanitize_value(None)) # Test None input

    def test_sanitize_numpy_floats(self):
        self.assertIsNone(sanitize_value(np.inf))
        self.assertIsNone(sanitize_value(np.nan))
        # Test with a numpy float that is finite
        self.assertEqual(sanitize_value(np.float64(10.0)), 10.0)
        self.assertEqual(sanitize_value(np.float32(5.0)), 5.0)


    def test_sanitize_list(self):
        input_list = [1.0, float('inf'), math.nan, np.inf, np.nan, 5.5, None]
        expected_list = [1.0, None, None, None, None, 5.5, None]
        self.assertEqual(sanitize_value(input_list), expected_list)

    def test_sanitize_numpy_array(self):
        # Test with a numpy array
        input_array = np.array([1.0, np.inf, np.nan, -np.inf, 3.0], dtype=np.float64)
        expected_list_from_array = [1.0, None, None, None, 3.0]
        self.assertEqual(sanitize_value(input_array), expected_list_from_array)

    def test_sanitize_dictionary(self):
        input_dict = {
            'a': float('inf'),
            'b': [2.0, math.nan, np.inf],
            'c': {'d': np.nan, 'e': 10.0},
            'f': None,
            'g': 25.0
        }
        expected_dict = {
            'a': None,
            'b': [2.0, None, None],
            'c': {'d': None, 'e': 10.0},
            'f': None,
            'g': 25.0
        }
        self.assertEqual(sanitize_value(input_dict), expected_dict)

    def test_sanitize_nested_structures(self):
        input_val = [
            {'key1': float('inf'), 'key2': [1, 2, math.nan, {'nested_key': np.inf}]},
            None,
            3.0
        ]
        expected_val = [
            {'key1': None, 'key2': [1, 2, None, {'nested_key': None}]},
            None,
            3.0
        ]
        self.assertEqual(sanitize_value(input_val), expected_val)

    def test_sanitize_non_problematic_values(self):
        self.assertEqual(sanitize_value(100), 100)
        self.assertEqual(sanitize_value("test_string"), "test_string")
        self.assertEqual(sanitize_value(True), True)
        self.assertEqual(sanitize_value([1, 2, "abc"]), [1, 2, "abc"])
        self.assertEqual(sanitize_value({'x': 1, 'y': "y_val"}), {'x': 1, 'y': "y_val"})

if __name__ == '__main__':
    unittest.main()
