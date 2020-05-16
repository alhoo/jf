"""Tests for the PYQ tool"""
# -*- coding: utf-8 -*-
import unittest
import json

from jf.query_parser import join_tokens, make_param_list, parse_part, parse_query


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
        expected = "demomodule.timestamppipe(),"
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def test_filter(self):
        """Test simple filter"""
        test_str = 'filter(x.id == "123")'
        expected = 'filter(x.id == "123"),'
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def test_filter2(self):
        """Test simple filter"""
        test_str = 'filter(x.commit.committer.name == "Lasse Hyyrynen")'
        expected = 'filter(x.commit.committer.name == "Lasse Hyyrynen"),'
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def test_filter_shortened(self):
        """Test simple filter"""
        test_str = '(x.id == "123")'
        expected = 'filter(x.id == "123"),'
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def test_map_shortened(self):
        """Test simple filter"""
        test_str = "{id: x.id}"
        expected = "map({ id:x.id }),"
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def test_map_filter(self):
        """Test simple filter"""
        test_str = 'map({id: x.id}), filter(x.id == "123")'
        expected = 'map({ id:x.id }),filter(x.id == "123"),'
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def test_simple(self):
        """Test simple query"""
        test_str = "map(x.id)"
        expected = "map(x.id),"
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def test_imported_class(self):
        test_str = (
            "demomod.Dup(int(age(x.c.author).total()/3), group=1)"
            + '.process(lambda x: {"dup": x.id})'
        )
        expected = (
            "demomod.Dup(int(age(x.c.author).total()/ 3), group = 1)"
            + '.process(lambda x : {"dup":x.id}),'
        )
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def _test_two(self):
        """Test simple query"""
        test_str = "map(x.id), sorted(x.id)"
        expected = "map(x.id), sorted(x.id),"
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def _test_keywords(self):
        """Test simple query"""
        test_str = "map(x.id), sorted(x.id, reverse=True)"
        expected = "map(x.id)," + "sorted(x.id, reverse = True),"
        result = parse_query(test_str)
        self.assertEqual(result, expected)
