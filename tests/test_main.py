"""Tests for the PYQ tool"""
# -*- coding: utf-8 -*-
import unittest

from io import StringIO
import logging

from jf.__main__ import set_loggers, main

def disable_loggers():
    logger = logging.getLogger('jf')
    logger.setLevel(logging.ERROR)

class TestJfMain(unittest.TestCase):
    """Basic jf main"""

    def test_main_jsonl(self):
        """Test log setting"""
        main(['I', 'test.jsonl'])
        #main(['', StringIO('{"a": 1}, {"a": 2}')])

    def test_main_json(self):
        """Test log setting"""
        main(['I', 'test.json'])
        #main(['', StringIO('{"a": 1}, {"a": 2}')])

    def test_main_yaml(self):
        """Test log setting"""
        main(['I', 'test.yaml'])
        #main(['', StringIO('{"a": 1}, {"a": 2}')])

    def test_logger_setting(self):
        """Test log setting"""
        set_loggers(False)
        set_loggers(True)
        disable_loggers()

