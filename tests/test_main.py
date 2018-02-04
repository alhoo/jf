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
        main(['--list', 'I', 'test.jsonl'])

    def test_main_help(self):
        """Test log setting"""
        with self.assertRaises(SystemExit):
            main(['--help'])

    def test_main_json(self):
        """Test log setting"""
        main(['--list', '--raw', '--yaml', 'I', 'test.json'])

    def test_main_json(self):
        """Test log setting"""
        main(['--raw', '--yaml', 'I', 'test.json'])

    def test_main_json(self):
        """Test log setting"""
        main(['--list', '--yaml', 'I', 'test.json'])

    def test_main_yaml(self):
        """Test log setting"""
        main(['I', 'test.yaml'])

    def test_main_yaml(self):
        """Test log setting"""
        main(['--yamli', 'I', 'test.yaml'])

    def test_logger_setting(self):
        """Test log setting"""
        set_loggers(False)
        set_loggers(True)
        disable_loggers()

