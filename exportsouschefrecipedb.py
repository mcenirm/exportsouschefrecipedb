import argparse
import os


def main(argv, out, err):
    ap = argparse.ArgumentParser(
        prog=argv[0],
    )
    ap.print_usage(file=err)
    return os.EX_USAGE


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv, out=sys.stdout, err=sys.stderr))
