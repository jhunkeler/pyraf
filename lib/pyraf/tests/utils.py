import os

from astropy.utils.data import get_pkg_data_contents


def diff_outputs(fin, reffile):
    """Compare output lines with reference file."""
    if isinstance(fin, list):
        lines = fin
    else:
        with open(fin) as f:
            lines = f.readlines()

    ans = get_pkg_data_contents(reffile).split(os.linesep)

    for x, y in zip(lines, ans):
        assert x.strip(os.linesep) == y, '{} : {}'.format(x, y)
