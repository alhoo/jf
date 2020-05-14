"""Tests for the PYQ tool"""
# -*- coding: utf-8 -*-
import unittest
import json

from jf.parser import join_tokens, make_param_list, parse_part, parse_query


class TestJfIO(unittest.TestCase):
    """Basic jf io testcases"""

    def test_param_list(self):
        test_item = [["x"], [["."], ["id"]]]
        expected = ["x.id"]
        result = make_param_list(test_item)
        self.assertEqual(result, expected)

    def test_parse_part(self):
        test_item = ["x", ".id"]
        expected = "x.id"
        result = parse_part(test_item)
        self.assertEqual(result, expected)

    def test_module_parse(self):
        """Test simple filter"""
        test_str = "demomodule.timestamppipe()"
        expected = "demomodule.timestamppipe(lambda x, *rest: ()),"
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def test_filter(self):
        """Test simple filter"""
        test_str = 'filter(x.id == "123")'
        expected = "filter(lambda x, " + '*rest: (x.id == "123")),'
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def test_filter2(self):
        """Test simple filter"""
        test_str = 'filter(x.commit.committer.name == "Lasse Hyyrynen")'
        expected = (
            "filter(lambda x, *rest: "
            + '(x.commit.committer.name == "Lasse Hyyrynen")),'
        )
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def test_filter_shortened(self):
        """Test simple filter"""
        test_str = '(x.id == "123")'
        expected = 'filter(lambda x, *rest: (x.id == "123")),'
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def test_map_shortened(self):
        """Test simple filter"""
        test_str = "{id: x.id}"
        expected = "map(lambda x, *rest: ({ id:x.id })),"
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def test_map_filter(self):
        """Test simple filter"""
        test_str = 'map({id: x.id}), filter(x.id == "123")'
        expected = (
            "map(lambda x, "
            + "*rest: ({ id:x.id })),"
            + "filter(lambda x, "
            + '*rest: (x.id == "123")),'
        )
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def test_simple(self):
        """Test simple query"""
        test_str = "map(x.id)"
        expected = "map(lambda x, *rest: (x.id)),"
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def test_imported_class(self):
        test_str = (
            "demomod.Dup(int(age(x.c.author).total()/3), group=1)"
            + '.process(lambda x: {"dup": x.id})'
        )
        expected = (
            "demomod.Dup(lambda x, *rest: "
            + "(int(age(x.c.author).total()/ 3)), group = 1)"
            + '.process(lambda x : {"dup":x.id}),'
        )
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def _test_two(self):
        """Test simple query"""
        test_str = "map(x.id), sorted(x.id)"
        expected = (
            "map(lambda x, *rest: (x.id)),"
            + "sorted(lambda x, *rest: (x.id)),"
        )
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def _test_keywords(self):
        """Test simple query"""
        test_str = "map(x.id), sorted(x.id, reverse=True)"
        expected = (
            "map(lambda x, *rest: (x.id)),"
            + "sorted(lambda x, *rest: (x.id), "
            + "reverse = True),"
        )
        result = parse_query(test_str)
        self.assertEqual(result, expected)
