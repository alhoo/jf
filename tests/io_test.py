"""Tests for the PYQ tool"""
# -*- coding: utf-8 -*-
import unittest
import json

from jf.io import read_jsonl_json_or_yaml, yield_json_and_json_lines


class TestJfIO(unittest.TestCase):
    """Basic jf io testcases"""

    def test_json(self):
        """Test simple query"""
        test_str = '[{"a": 2353}, {"a": 646}]'
        result = list(yield_json_and_json_lines([test_str]))
        self.assertEqual(result, ['{"a": 2353}', '{"a": 646}'])

    def test_jsonl(self):
        """Test simple query"""
        test_str = '{"a": 2353}, {"a": 646}'
        result = list(yield_json_and_json_lines([test_str]))
        self.assertEqual(result, ['{"a": 2353}', '{"a": 646}'])

    def test_weird_json(self):
        """Test simple query"""
        test_str = '["a", {"a": 2353}, {"a": 646}]'
        result = list(yield_json_and_json_lines([test_str]))
        self.assertEqual(result, ['"a"', '{"a": 2353}', '{"a": 646}'])

    def test_weird_jsonl(self):
        """Test simple query"""
        test_str = '"a", {"a": 2353}, {"a": 646}'
        result = list(yield_json_and_json_lines([test_str]))
        self.assertEqual(result, ['"a"', '{"a": 2353}', '{"a": 646}'])

    def test_escaped_json(self):
        """Test simple query"""
        test_str = '["a", {"a": 2353, "b": "sdaf\\"}f32"}, {"a": 646}]'
        result = list(yield_json_and_json_lines([test_str]))
        expected = ['"a"', '{"a": 2353, "b": "sdaf\\"}f32"}', '{"a": 646}']
        self.assertEqual(result, expected)

    def test_escaped_jsonl(self):
        """Test simple query"""
        test_str = '"a", {"a": 2353, "b": "sdaf\\"}f32"}, {"a": 646}'
        result = list(yield_json_and_json_lines([test_str]))
        expected = ['"a"', '{"a": 2353, "b": "sdaf\\"}f32"}', '{"a": 646}']
        self.assertEqual(result, expected)

    def test_escaped_json_2(self):
        """Test simple query"""
        test_obj = ["a", {"a": 2353, "b": "sdaf\"}f32"}, {"a": 646}]
        test_str = json.dumps(test_obj, sort_keys=True)
        result = list(yield_json_and_json_lines([test_str]))
        expected = ['"a"', '{"a": 2353, "b": "sdaf\\"}f32"}', '{"a": 646}']
        self.assertEqual(result, expected)

    def test_escaped_jsonl_2(self):
        """Test simple query"""
        test_obj = ["a", {"a": 2353, "b": "sdaf\"}f32"}, {"a": 646}]
        test_str = json.dumps(test_obj, sort_keys=True)
        result = list(yield_json_and_json_lines([test_str]))
        expected = ['"a"', '{"a": 2353, "b": "sdaf\\"}f32"}', '{"a": 646}']
        self.assertEqual(result, expected)
