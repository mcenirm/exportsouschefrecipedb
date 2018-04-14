from subprocess import Popen, PIPE
import unittest

import exportsouschefrecipedb


class ModuleTest(unittest.TestCase):
    def test_main_no_args(self):
        with self.assertRaises(NotImplementedError):
            exportsouschefrecipedb.main([], None, None)

    def test_module_as_script(self):
        proc = Popen(
            ['python', '-m', 'exportsouschefrecipedb', 'potato'],
            stdout=PIPE,
            stderr=PIPE,
        )
        outs, errs = proc.communicate()
        rc = proc.wait()
        self.assertEqual(0, rc, msg=str(errs))