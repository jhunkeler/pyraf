"""These were tests under core/irafparlist and core/subproc in pandokia."""
from __future__ import absolute_import, division

import pytest

from .utils import diff_outputs, HAS_IRAF

if HAS_IRAF:
    from pyraf import irafpar


@pytest.mark.skipif(not HAS_IRAF, reason='Need IRAF to run')
def test_irafparlist(tmpdir):
    outfile = str(tmpdir.join('output.txt'))

    with open(outfile, 'w') as f:
        irafpar.test_IrafParList(f)

    diff_outputs(outfile, 'data/core_irafparlist_output.ref')


@pytest.mark.skipif(not HAS_IRAF, reason='Need IRAF to run')
def test_subproc():
    pass
