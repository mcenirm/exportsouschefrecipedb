import subprocess
import unittest
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

import exportsouschefrecipedb


ARGPARSE_EX_USAGE = 2


def _main(argv):
    outs = ''
    errs = ''
    with StringIO() as out, StringIO() as err:
        rc = exportsouschefrecipedb.main(argv, out=out, err=err)
        outs = out.getvalue()
        errs = err.getvalue()
    return (rc, outs, errs)


class TestExportSouschefRecipedb(unittest.TestCase):
    def test_none_args(self):
        output = exportsouschefrecipedb.export_souschef_recipedb(
            None,
            None,
            source_class=None,
            output_class=None,
            exporter_class=None,
        )
        self.assertIsNone(output)


class TestMain(unittest.TestCase):

    def test_no_args(self):
        with self.assertRaises(SystemExit) as raised:
            _main(['placeholder'])
        self.assertEqual(ARGPARSE_EX_USAGE, raised.exception.code)


class TestModuleAsScript(unittest.TestCase):
    def test_no_args(self):
        proc = subprocess.Popen(
            ['python', '-m', 'exportsouschefrecipedb'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        outs, errs = proc.communicate()
        rc = proc.wait()
        self.assertEqual(ARGPARSE_EX_USAGE, rc, msg=str(errs))
