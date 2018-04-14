import argparse
import os


def export_souschef_recipedb(path_to_recipedb_file, path_to_output_folder):
    raise NotImplementedError()


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
