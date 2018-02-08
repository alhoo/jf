from distutils.core import setup, Extension

module1 = Extension('jsonl_io',
                    sources = ['jf/io.c'])

setup (name = 'JsonLineParser',
       version = '1.0',
       description = 'This is a jsonl package',
       ext_modules = [module1])

