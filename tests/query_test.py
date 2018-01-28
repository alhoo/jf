# -*- coding: utf-8 -*-
import unittest

#from pyq import run_query
import pyq
import json

def tolist(igen):
  return json.dumps([x for x in igen], sort_keys=True)

class Test_pyq(unittest.TestCase):

    def test_simple_query(self):
        """Test simple query"""

        data = [{"a": 1}]
        self.assertEqual(tolist(pyq.run_query("map(x.a)", data)), '[1]')

    def test_complex_query(self):
        """Test complex query"""

        data = [{"a": 1, 'b': {'c': 632, 'd': [1,2,3,4]}}]
        cmd = 'map({"id": x.a, "data": x.b.d})'
        result = '[{"data": [1, 2, 3, 4], "id": 1}]'
        self.assertEqual(tolist(list(pyq.run_query(cmd, data, sort_keys=True))), result)

    def test_non_json_query(self):
        """Test complex query"""

        data = [{"a": 1, 'b': {'c': 632, 'd': [1,2,3,4]}}]
        cmd = 'map({id: x.a, data: x.b.d})'
        result = '[{"data": [1, 2, 3, 4], "id": 1}]'
        self.assertEqual(tolist(pyq.run_query(cmd, data, sort_keys=True)), result)

