# -*- coding: utf-8 -*-
import unittest

#from pyq import run_query
import pyq


class Test_pyq(unittest.TestCase):

    def test_simple_query(self):
        """Load all the test files to be processes"""

        data = {"a": 1}
        self.assertEqual(pyq.run_query("x.a", data), '1')

