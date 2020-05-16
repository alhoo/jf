"""Tests for the JF library"""
# -*- coding: utf-8 -*-
import unittest
from jf.process import Col, Map
        
x = Col()

class TestJfMainTransformation(unittest.TestCase):
    """Basic jf io testcases"""
    def test_map_001(self):
        t = Map(x.id)
        result = t.transform([{"id": 1}])
        expected = [1]
        self.assertEqual(result, expected)
    
    def test_map_002(self):
        t = Map({"id": x.id, "b": x.a.b[4]})
        result = t.transform([{"id": 1, "a": {"b": [1,2,3,4,5,6]}}])
        expected = [{'id': 1, 'b': 5}]
        self.assertEqual(result, expected)
