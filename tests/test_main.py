"""Tests for the PYQ tool"""
# -*- coding: utf-8 -*-
import unittest

import sys
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
        main(['--indent=-1', 'I', 'tests/test.json'])

    def test_main_jsonl2(self):
        """Test log setting"""
        main(['--list', 'I', 'tests/test.jsonl'])

    def test_main_help(self):
        """Test log setting"""
        with self.assertRaises(SystemExit):
            main(['--help'])

    def test_main_json(self):
        """Test log setting"""
        main(['--list', '--raw', '--yaml', 'I', 'tests/test.json'])

    def test_main_json_raw(self):
        """Test log setting"""
        main(['--raw', '--yaml', 'I', 'tests/test.json'])

    def test_main_json_list(self):
        """Test log setting"""
        main(['--list', '--yaml', 'I', 'tests/test.json'])

    def test_main_yaml(self):
        """Test log setting"""
        main(['-'])

    def test_main_yaml(self):
        """Test log setting"""
        main(['I', 'tests/test.yaml'])

    def test_main_yaml_ipy(self):
        """Test log setting"""
        sys.stdin = StringIO("quit\n")
        main(['--ipyfake', 'I', 'tests/test.yaml'])

    def test_main_input_arg(self):
        """Test log setting"""
        main(['--input', 'tests/test.yaml', 'I'])

    def test_main_yaml_input(self):
        """Test log setting"""
        main(['--yamli', 'I', 'tests/test.yaml'])

    def test_logger_setting(self):
        """Test log setting"""
        set_loggers(False)
        set_loggers(True)
        disable_loggers()

