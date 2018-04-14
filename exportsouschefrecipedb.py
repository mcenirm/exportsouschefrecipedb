import argparse
import os


class RecipeDB():
    def __init__(self, path_to_recipedb_file):
        pass


class OutputFolder():
    def __init__(self, path_to_nonexistant_folder):
        pass


class Exporter():
    def export(self, source, output):
        pass


def export_souschef_recipedb(
    path_to_recipedb_file,
    path_to_output_folder,
    source_class=None,
    output_class=None,
    exporter_class=None,
):
    if source_class is None:
        source_class = RecipeDB
    if output_class is None:
        output_class = OutputFolder
    if exporter_class is None:
        exporter_class = Exporter

    if path_to_recipedb_file is None:
        return None
    if path_to_output_folder is None:
        return None

    source = source_class(path_to_recipedb_file=path_to_recipedb_file)
    output = output_class(path_to_nonexistant_folder=path_to_output_folder)
    exporter = exporter_class()
    exporter.export(source, output)

    return output


def main(argv, out, err):
    ap = argparse.ArgumentParser(
        prog=argv[0],
    )
    ap.add_argument('recipedbfile')
    ap.add_argument('outputfolder')
    args = ap.parse_args(args=argv[1:])
    export_souschef_recipedb(
        path_to_recipedb_file=args.recipedbfile,
        path_to_output_folder=args.outputfolder,
    )
    return os.EX_OK


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv, out=sys.stdout, err=sys.stderr))
