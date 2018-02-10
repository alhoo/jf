"""Tests for the PYQ tool"""
# -*- coding: utf-8 -*-
import unittest

import sys
from io import StringIO
import logging

from jf.__main__ import set_loggers, main

from contextlib import contextmanager
from io import StringIO

def disable_loggers():
    logger = logging.getLogger('jf')
    logger.setLevel(logging.ERROR)

@contextmanager
def captured_output(write_to=StringIO):
    new_out, new_err = write_to(), write_to
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class BrokenPipeOutput:
    def isatty(self):
        return True

    def write(self, s):
        raise BrokenPipeError


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
        with captured_output(BrokenPipeOutput) as (out, err):
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

