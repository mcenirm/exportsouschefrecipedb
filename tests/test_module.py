from subprocess import Popen, PIPE
import unittest


class ModuleTest(unittest.TestCase):
    def test_module_as_script(self):
        proc = Popen(
            ['python', '-m', 'exportsouschefrecipedb', 'potato'],
            stdout=PIPE,
            stderr=PIPE,
        )
        outs, errs = proc.communicate()
        rc = proc.wait()
        self.assertEqual(0, rc, msg=str(errs))
