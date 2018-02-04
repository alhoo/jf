"""Tests for the PYQ tool"""
# -*- coding: utf-8 -*-
import unittest
import json

from jf.parser import join_tokens, make_param_list, parse_part, parse_query


class TestJfIO(unittest.TestCase):
    """Basic jf io testcases"""

    def test_param_list(self):
        test_item = [['x'], [['.'], ['id']]]
        expected = ['x.id']
        result = make_param_list(test_item)
        self.assertEqual(result, expected)

    def test_parse_part(self):
        test_item = ['x', '.id']
        expected = 'lambda arr: x.id'
        result = parse_part(test_item)
        self.assertEqual(result, expected)

    def test_filter(self):
        """Test simple filter"""
        test_str = 'filter(x.id == "123")'
        expected = 'lambda arr: filter(lambda x, *rest: (x.id == "123"), arr),'
        result = parse_query(test_str)
        self.assertEqual(result, expected)


    def test_filter(self):
        """Test simple filter"""
        test_str = 'filter(x.commit.committer.name == "Lasse Hyyrynen")'
        expected = 'lambda arr: filter(lambda x, *rest: (x.commit.committer.name == "Lasse Hyyrynen"), arr),'
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def test_map_filter(self):
        """Test simple filter"""
        test_str = 'map({id: x.id}), filter(x.id == "123")'
        expected = 'lambda arr: map(lambda x, *rest: ({ id:x.id }), arr),lambda arr: filter(lambda x, *rest: (x.id == "123"), arr),'
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def test_simple(self):
        """Test simple query"""
        test_str = 'map(x.id)'
        expected = 'lambda arr: map(lambda x, *rest: (x.id), arr),'
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def _test_two(self):
        """Test simple query"""
        test_str = 'map(x.id), sorted(x.id)'
        expected = 'lambda arr: map(lambda x, *rest: (x.id), arr),' + \
                   'lambda arr: sorted(lambda x, *rest: (x.id), arr),'
        result = parse_query(test_str)
        self.assertEqual(result, expected)

    def _test_keywords(self):
        """Test simple query"""
        test_str = 'map(x.id), sorted(x.id, reverse=True)'
        expected = 'lambda arr: map(lambda x, *rest: (x.id), arr),' + \
                   'lambda arr: sorted(lambda x, *rest: (x.id), arr, ' + \
                   'reverse = True),'
        result = parse_query(test_str)
        self.assertEqual(result, expected)
