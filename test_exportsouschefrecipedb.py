from subprocess import Popen, PIPE
import unittest

import exportsouschefrecipedb


class ModuleTest(unittest.TestCase):
    def test_main_no_args(self):
        with self.assertRaises(NotImplementedError):
            exportsouschefrecipedb.main([], None, None)

    def test_module_as_script(self):
        with self.assertRaises(NotImplementedError):
            proc = Popen(
                ['python', '-m', 'exportsouschefrecipedb', 'potato'],
                stdout=PIPE,
                stderr=PIPE,
            )
            proc.communicate()
            proc.wait()
