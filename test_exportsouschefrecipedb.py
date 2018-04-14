from subprocess import Popen, PIPE
import unittest

import exportsouschefrecipedb


class TestMain(unittest.TestCase):
    def test_no_args(self):
        with self.assertRaises(NotImplementedError):
            exportsouschefrecipedb.main([], None, None)


class TestModuleAsScript(unittest.TestCase):
    def test_no_args(self):
        proc = Popen(
            ['python', '-m', 'exportsouschefrecipedb'],
            stdout=PIPE,
            stderr=PIPE,
        )
        outs, errs = proc.communicate()
        rc = proc.wait()
        self.assertNotEqual(0, rc, msg=str(errs))
