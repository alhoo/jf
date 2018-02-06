"""Tests for the PYQ tool"""
# -*- coding: utf-8 -*-
import unittest
import json

from datetime import datetime, date

import jf


def tolist(igen):
    """Convert gen to list"""
    return json.dumps([x for x in igen], cls=jf.StructEncoder, sort_keys=True)


class TestJfGenProcessor(unittest.TestCase):
    """Basic jf io testcases"""

    def test_param_list(self):
        gp = jf.GenProcessor((1,2,3), [lambda arr: map(lambda x: 2*x, arr)])
        gp.add_filter(lambda arr: map(lambda x: 2*x, arr))
        self.assertEqual(list(gp.process()), [4,8,12])


class TestJfFunctions(unittest.TestCase):
    """Basic jf functions"""

    def test_result_cleaner(self):
        """Test peeking"""
        st = jf.Struct(**{"a": 3})
        res = jf.result_cleaner([st])
        self.assertEqual(res, [{"a": 3}])

    def test_result_cleaner(self):
        """Test peeking"""
        st = jf.Struct(**{"a": datetime(2018, 1, 1)})
        res = jf.result_cleaner([st])
        self.assertEqual(res, [{"a": '2018-01-01 00:00:00'}])

    def test_peek(self):
        """Test peeking"""
        data = [1,2,3]
        head, data = jf.peek(data, 1)
        self.assertEqual(head, [1])
        self.assertEqual(list(data), [1, 2,3])

    def test_peek_2(self):
        """Test peeking"""
        data = [1,2,3]
        head, data = jf.peek(data, 2)
        self.assertEqual(head, [1, 2])
        self.assertEqual(list(data), [1, 2,3])

    def test_dateparser(self):
        """Test date parsing"""
        result = jf.parse_value("2018-01-01")
        expected = datetime(2018, 1, 1, 0, 0)
        self.assertEqual(result, expected)

    def test_dateparser_nondate(self):
        """Test date parsing"""
        result = jf.parse_value({"not": "a date"})
        expected = {"not": "a date"}
        self.assertEqual(result, expected)

    def test_dateparser_empty(self):
        """Test date parsing"""
        result = jf.parse_value("")
        expected = ""
        self.assertEqual(result, expected)

    def test_dateparser_nondate(self):
        """Test date parsing"""
        result = jf.parse_value("n")
        expected = "n"
        self.assertEqual(result, expected)

    def test_dateparser_nondate(self):
        """Test date parsing"""
        result = jf.parse_value("not a date")
        expected = "not a date"
        self.assertEqual(result, expected)

    def test_reduce_list(self):
        result = jf.reduce_list(None, [1,2])
        expected = [[1,2]]
        self.assertEqual(result, expected)

    def test_colorize(self):
        result = None
        try:
          query = "{x.id]"
          query = jf.parse_query(query).rstrip(",")
        except SyntaxError as ex:
          print(ex)
          result = jf.colorize(ex)
          pass
        expected = '{x.id'+jf.RED+']'+jf.RESET+','
        self.assertEqual(result, expected)


class TestJf(unittest.TestCase):
    """Basic jf testcases"""

    def test_ipython(self):
        """Test simple query"""

        jf.ipy(None, [1,2,3], fakerun=True)

    def test_get_item(self):
        """Test simple query"""

        data = [{"a": 1}]
        self.assertEqual(tolist(jf.run_query('map(x["a"])', data)), '[1]')

    def test_get_null_item(self):
        """Test simple query"""

        data = [{"a": 1}]
        self.assertEqual(tolist(jf.run_query('map(x["b"])', data)), '[null]')

    def test_simple_query(self):
        """Test simple query"""

        data = [{"a": 1}]
        self.assertEqual(tolist(jf.run_query("map(x.a)", data)), '[1]')

    def test_hide_many(self):
        """Test complex query"""

        data = [{"a": 1, 'b': {'c': 632, 'd': [1, 2, 3, 4]}},
                {"a": 2, "f": 4, 'b': {'c': 632, 'd': [1, 2, 3, 4]}}]
        cmd = 'map({"id": x.a, "c": x.b.c, "data": x.b.d, "x": x["f"]}),' + \
              'hide("data", "c")'
        expected = '[{"id": 1, "x": null}, {"id": 2, "x": 4}]'
        result = tolist(list(jf.run_query(cmd, data)))
        self.assertEqual(result, expected)

    def test_hide(self):
        """Test complex query"""

        data = [{"a": 1, 'b': {'c': 632, 'd': [1, 2, 3, 4]}}]
        cmd = 'map({"id": x.a, "data": x.b.d}), hide("data")'
        expected = '[{"id": 1}]'
        result = tolist(list(jf.run_query(cmd, data, "itertools")))
        self.assertEqual(result, expected)

    def test_complex_query(self):
        """Test complex query"""

        data = [{"a": 1, 'b': {'c': 632, 'd': [1, 2, 3, 4]}}]
        cmd = 'map({"id": x.a, "data": x.b.d})'
        expected = '[{"data": [1, 2, 3, 4], "id": 1}]'
        result = tolist(list(jf.run_query(cmd, data)))
        self.assertEqual(result, expected)

    def test_query_syntax_error(self):
        """Test complex query"""

        data = [{"a": 1, 'b': {'c': 632, 'd': [1, 2, 3, 4]}}]
        cmd = 'map({id: x.a, data: x.b.d'
        expected = '[{"data": [1, 2, 3, 4], "id": 1}]'
        with  self.assertRaises(SyntaxError):
          result = tolist(list(jf.run_query(cmd, data)))

    def test_non_json_query(self):
        """Test complex query"""

        data = [{"a": 1, 'b': {'c': 632, 'd': [1, 2, 3, 4]}}]
        cmd = 'map({id: x.a, data: x.b.d})'
        expected = '[{"data": [1, 2, 3, 4], "id": 1}]'
        result = tolist(list(jf.run_query(cmd, data)))
        self.assertEqual(result, expected)

    def test_filter_query(self):
        """Test complex query"""

        data = [{"a": 2, 'b': {'c': 632, 'd': [1, 2, 3, 4]}},
                {"a": 1, 'b': {'c': 632, 'd': [3, 4, 5, 6]}},
                {"a": 5, 'b': {'c': 632, 'd': [5, 6, 7, 8]}}]
        cmd = 'map({id: x.a, data: x.b.d[0]}), filter(.id > 1)'
        expected = '[{"data": 1, "id": 2}, {"data": 5, "id": 5}]'
        result = tolist(list(jf.run_query(cmd, data)))
        self.assertEqual(result, expected)

    def test_sorting_query(self):
        """Test complex query"""

        data = [{"a": 2, 'b': {'c': 632, 'd': [1, 2, 3, 4]}},
                {"a": 1, 'b': {'c': 632, 'd': [3, 4, 5, 6]}},
                {"a": 5, 'b': {'c': 632, 'd': [5, 6, 7, 8]}}]
        cmd = 'map({id: x.a, data: x.b.d[0]}), sorted(.id, reverse=True)'
        expected = '[{"data": 5, "id": 5}, {"data": 1, "id": 2}, ' + \
                   '{"data": 3, "id": 1}]'
        result = tolist(list(jf.run_query(cmd, data)))
        self.assertEqual(result, expected)

    def test_age(self):
        """
        $ cat test.yaml | jf --yamli
            'map(x.update({id: x.sha, age: age(x.commit.author.date)})),
             filter(x.age < age("1 days"))' --indent=2 --yaml
        """

        data = [{"a": 2, 'b': "2018-01-30 16:28:40+00:00"},
                {"a": 1, 'b': "2018-01-30 15:12:35+00:00"},
                {"a": 3, 'b': "2018-01-10 15:12:35+00:00"},
                {"a": 5, 'b': "2018-01-30 16:06:59+00:00"}]
        cmd = 'map({id: x.a, date: x.b}),' + \
              'sorted(age(.date), reverse=True),' + \
              'map(.id)'
        expected = '[3, 1, 5, 2]'
        result = tolist(list(jf.run_query(cmd, data)))
        self.assertEqual(result, expected)

    def test_age_output(self):
        """
        $ cat test.yaml | jf --yamli
            'map(x.update({id: x.sha, age: age(x.commit.author.date)})),
             filter(x.age < age("1 days"))' --indent=2 --yaml
        """

        data = [{"a": 2, 'b': "2018-01-30 16:28:40+00:00"},
                {"a": 1, 'b': "2018-01-30 15:12:35+00:00"}]
        cmd = 'map({id: x.a, date: x.b}),' + \
              'sorted(age(.date), reverse=True), first()'
        expected = '[{"date": "2018-01-30 15:12:35+00:00", "id": 1}]'
        result = tolist(list(jf.run_query(cmd, data)))
        self.assertEqual(result, expected)

    def test_age_output_2(self):
        """
        $ cat test.yaml | jf --yamli
            'map(x.update({id: x.sha, age: age(x.commit.author.date)})),
             filter(x.age < age("1 days"))' --indent=2 --yaml
        """

        data = [{"a": 2, 'b': "2018-01-30 16:28:40+00:00"},
                {"a": 1, 'b': "2018-01-30 15:12:35+00:00"}]
        cmd = 'map({id: x.a, date: x.b}),' + \
              'sorted(age(.date), reverse=True),' + \
              'map(.date)'
        expected = '["2018-01-30 15:12:35+00:00", "2018-01-30 16:28:40+00:00"]'
        result = tolist(list(jf.run_query(cmd, data)))
        self.assertEqual(result, expected)

    def test_age_tz(self):
        """Test age with items containing differing timezones"""
        data = [{"a": 2, 'b': "2018-01-30 16:28:40+00:00"},
                {"a": 1, 'b': "2018-01-30 15:12:35+00:00"},
                {"a": 3, 'b': "2018-01-10 15:12:35+00:00"},
                {"a": 5, 'b': "2018-01-30 16:06:59+03:00"}]
        cmd = 'map({id: x.a, date: x.b}),' + \
              'sorted(age(.date), reverse=True), map(.id)'
        expected = '[3, 5, 1, 2]'
        result = tolist(list(jf.run_query(cmd, data)))
        self.assertEqual(result, expected)

    def test_islice_1(self):
        """Test islicing data"""
        data = [{"a": 2, 'b': "2018-01-30 16:28:40+00:00"},
                {"a": 1, 'b': "2018-01-30 15:12:35+00:00"},
                {"a": 3, 'b': "2018-01-10 15:12:35+00:00"},
                {"a": 5, 'b': "2018-01-30 16:06:59+03:00"}]
        cmd = 'map({id: x.a, date: x.b}),' + \
              'sorted(age(.date), reverse=True), map(.id), islice(1)'
        expected = '[3]'
        result = tolist(list(jf.run_query(cmd, data)))
        self.assertEqual(result, expected)

    def test_islice_2(self):
        """Test islicing data"""
        data = [{"a": 2, 'b': "2018-01-30 16:28:40+00:00"},
                {"a": 1, 'b': "2018-01-30 15:12:35+00:00"},
                {"a": 3, 'b': "2018-01-10 15:12:35+00:00"},
                {"a": 5, 'b': "2018-01-30 16:06:59+03:00"}]
        cmd = 'map({id: x.a, date: x.b}),' + \
              'sorted(age(.date), reverse=True), map(.id), islice(1, 2)'
        expected = '[5]'
        result = tolist(list(jf.run_query(cmd, data)))
        self.assertEqual(result, expected)

    def test_islice(self):
        """Test islicing data"""
        data = [{"a": 2, 'b': "2018-01-30 16:28:40+00:00"},
                {"a": 1, 'b': "2018-01-30 15:12:35+00:00"},
                {"a": 3, 'b': "2018-01-10 15:12:35+00:00"},
                {"a": 5, 'b': "2018-01-30 16:06:59+03:00"}]
        cmd = 'map({id: x.a, date: x.b}),' + \
              'sorted(age(.date), reverse=True), map(.id), islice(1, 4, 2)'
        expected = '[5, 2]'
        result = tolist(list(jf.run_query(cmd, data)))
        self.assertEqual(result, expected)

    def test_last(self):
        """Test fetching last items"""
        data = [{"a": 2, 'b': "2018-01-30 16:28:40+00:00"},
                {"a": 1, 'b': "2018-01-30 15:12:35+00:00"},
                {"a": 3, 'b': "2018-01-10 15:12:35+00:00"},
                {"a": 5, 'b': "2018-01-30 16:06:59+03:00"}]
        cmd = 'map({id: x.a, date: x.b}),' + \
              'sorted(age(.date), reverse=True), map(.id), last()'
        expected = '[2]'
        result = tolist(list(jf.run_query(cmd, data)))
        self.assertEqual(result, expected)

    def test_last_2(self):
        """Test fetching last items"""
        data = [{"a": 2, 'b': "2018-01-30 16:28:40+00:00"},
                {"a": 1, 'b': "2018-01-30 15:12:35+00:00"},
                {"a": 3, 'b': "2018-01-10 15:12:35+00:00"},
                {"a": 5, 'b': "2018-01-30 16:06:59+03:00"}]
        cmd = 'map({id: x.a, date: x.b}),' + \
              'sorted(age(.date), reverse=True), map(.id), last(2)'
        expected = '[1, 2]'
        result = tolist(list(jf.run_query(cmd, data)))
        self.assertEqual(result, expected)

    def test_first(self):
        """Test fetching first items"""
        data = [{"a": 2, 'b': "2018-01-30 16:28:40+00:00"},
                {"a": 1, 'b': "2018-01-30 15:12:35+00:00"},
                {"a": 3, 'b': "2018-01-10 15:12:35+00:00"},
                {"a": 5, 'b': "2018-01-30 16:06:59+03:00"}]
        cmd = 'map({id: x.a, date: x.b}),' + \
              'sorted(age(.date), reverse=True), map(.id), first()'
        expected = '[3]'
        result = tolist(list(jf.run_query(cmd, data)))
        self.assertEqual(result, expected)

    def test_last_two_with_sort(self):
        """Test fetching last two items using sort and first"""
        data = [{"a": 2, 'b': "2018-01-30 16:28:40+00:00"},
                {"a": 1, 'b': "2018-01-30 15:12:35+00:00"},
                {"a": 3, 'b': "2018-01-10 15:12:35+00:00"},
                {"a": 5, 'b': "2018-01-30 16:06:59+03:00"}]
        cmd = 'map({id: x.a, date: x.b}),' + \
              'sorted(age(.date), reverse=False), map(.id), first(2)'
        expected = '[2, 1]'
        result = tolist(list(jf.run_query(cmd, data)))
        self.assertEqual(result, expected)
