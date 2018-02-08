"""Tests for the PYQ tool"""
# -*- coding: utf-8 -*-
import unittest
import json
import yaml

from io import StringIO

from jf.io import read_jsonl_json_or_yaml, yield_json_and_json_lines, print_results
from jf import Struct


class TestJfIO(unittest.TestCase):
    """Basic jf io testcases"""

    def test_json(self):
        """Test simple query"""
        test_str = '"a"'
        result = list(yield_json_and_json_lines([test_str]))
        self.assertEqual(result, ['"a"'])

    def test_print_result_list(self):
        """Test simple query"""
        args = Struct(**{"list": 1, "raw": 0, "html_unescape":1, "bw": 0, "forcecolor": 1})
        print_results([1,2], args)

    def test_print_result_list_2(self):
        """Test simple query"""
        args = Struct(**{"list": 1, "raw": 1, "html_unescape":1, "bw": 0, "forcecolor": 1})
        print_results(["a"], args)

    def test_print_result_list_3(self):
        """Test simple query"""
        args = Struct(**{"list": 1, "raw": 1, "html_unescape":1, "bw": 0, "forcecolor": 1})
        print_results([{"a": 1}], args)

    def test_print_results(self):
        """Test simple query"""
        args = Struct(**{"raw": 0, "html_unescape":1, "bw": 0, "forcecolor": 1})
        print_results([1,2], args)

    def test_print_results_2(self):
        """Test simple query"""
        args = Struct(**{"raw": 1, "html_unescape":1, "bw": 0, "forcecolor": 1})
        print_results(["a"], args)

    def test_print_results_3(self):
        """Test simple query"""
        args = Struct(**{"raw": 1, "html_unescape":1, "bw": 0, "forcecolor": 1})
        print_results([{"a": 1}], args)

    def test_json_2(self):
        """Test simple query"""
        test_str = '[{"a": 2353}, {"a": 646}]'
        result = list(yield_json_and_json_lines([test_str]))
        self.assertEqual(result, ['{"a": 2353}', '{"a": 646}'])

    def test_jsonl_list_of_lists(self):
        """Test simple query"""
        test_str = '[["a","b"],["c","d"]]'
        result = list(yield_json_and_json_lines([test_str]))
        self.assertEqual(result, ['["a","b"]', '["c","d"]'])

    def test_jsonl(self):
        """Test simple query"""
        test_str = '{"a": 2353}, {"a": 646}'
        result = list(yield_json_and_json_lines([test_str]))
        self.assertEqual(result, ['{"a": 2353}', '{"a": 646}'])

    def test_broken_jsonl_file(self):
        """Test simple query"""
        args = Struct(**{'files': 'input.json', "yamli": 0})
        def openhook(a=None, b=None):
          test_str = '{"a": 1, b: 5}\n{"a": 2, "b": 5}'
          return StringIO(test_str)
        result = list(read_jsonl_json_or_yaml(yaml.load, args, openhook=openhook))
        self.assertEqual(result, [{"a": 2, "b": 5}])

    def test_broken_yaml_file(self):
        """Test simple query"""
        args = Struct(**{'files': 'input.yaml', "yamli": 1})
        def openhook(a=None, b=None):
          test_str = '[a,b,c'
          return StringIO(test_str)
        result = list(read_jsonl_json_or_yaml(yaml.load, args, openhook=openhook))
        self.assertEqual(result, [])

    def test_jsonl_file(self):
        """Test simple query"""
        args = Struct(**{'files': 'input.json', "yamli": 0})
        def openhook(a=None, b=None):
          test_str = '{"a": 1}\n{"a": 2}'
          return StringIO(test_str)
        result = list(read_jsonl_json_or_yaml(yaml.load, args, openhook=openhook))
        #result = None
        #print(openhook().read())
        self.assertEqual(result, [{'a': 1}, {'a': 2}])

    def test_json_file(self):
        """Test simple query"""
        args = Struct(**{'files': 'input.json', "yamli": 0})
        def openhook(a=None, b=None):
          test_str = '["list"]'
          return StringIO(test_str)
        result = list(read_jsonl_json_or_yaml(yaml.load, args, openhook=openhook))
        #result = None
        #print(openhook().read())
        self.assertEqual(result, ['list'])

    def test_yaml_string(self):
        """Test simple query"""
        args = Struct(**{'files': 'input.yaml', "yamli": 1})
        def openhook(a=None, b=None):
          test_str = 'a'
          return StringIO(test_str)
        result = list(read_jsonl_json_or_yaml(yaml.load, args, openhook=openhook))
        #result = None
        #print(openhook().read())
        self.assertEqual(result, ['a'])

    def test_yaml_file(self):
        """Test simple query"""
        args = Struct(**{'files': 'input.yaml', "yamli": 1})
        def openhook(a=None, b=None):
          test_str = '- list'
          return StringIO(test_str)
        result = list(read_jsonl_json_or_yaml(yaml.load, args, openhook=openhook))
        #result = None
        #print(openhook().read())
        self.assertEqual(result, ['list'])

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

    def test_char_as_json(self):
        """Test simple query"""
        test_str = '"a"'
        result = list(yield_json_and_json_lines([test_str]))
        expected = ['"a"']
        self.assertEqual(result, expected)

    def test_escaped_jsonl_2(self):
        """Test simple query"""
        test_obj = ["a", {"a": 2353, "b": "sdaf\"}f32"}, {"a": 646}]
        test_str = json.dumps(test_obj, sort_keys=True)
        result = list(yield_json_and_json_lines([test_str]))
        expected = ['"a"', '{"a": 2353, "b": "sdaf\\"}f32"}', '{"a": 646}']
        self.assertEqual(result, expected)
