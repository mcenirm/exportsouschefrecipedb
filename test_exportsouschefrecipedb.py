import os
import subprocess
import unittest

import exportsouschefrecipedb


class TestMain(unittest.TestCase):
    def test_no_args(self):
        rc = exportsouschefrecipedb.main([], out=None, err=None)
        self.assertEqual(os.EX_USAGE, rc)


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
