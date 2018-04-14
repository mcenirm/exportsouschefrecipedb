import os


def main(argv, out, err):
    return os.EX_USAGE


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv, out=sys.stdout, err=sys.stderr))
