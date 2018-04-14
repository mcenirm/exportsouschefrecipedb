import os
import subprocess
import unittest
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

import exportsouschefrecipedb


class TestMain(unittest.TestCase):
    def test_no_args(self):
        placeholder = 'placeholder'
        expected_usage_start = 'usage: {0} '.format(placeholder)
        argv = [placeholder]
        with StringIO() as out, StringIO() as err:
            rc = exportsouschefrecipedb.main(argv, out=out, err=err)
            self.assertEqual(os.EX_USAGE, rc)
            errs = str(err.getvalue())
            self.assertTrue(errs.startswith(expected_usage_start))


class TestModuleAsScript(unittest.TestCase):
    def test_no_args(self):
        proc = subprocess.Popen(
            ['python', '-m', 'exportsouschefrecipedb'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        outs, errs = proc.communicate()
        rc = proc.wait()
        self.assertEqual(os.EX_USAGE, rc, msg=str(errs))
