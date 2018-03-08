#!/usr/bin/env python
#
from .utils import HAS_IRAF, DATA_DIR

import math
import os
import pytest
import subprocess

if HAS_IRAF:
    os.environ['PYRAF_NO_DISPLAY'] = '1'
    from pyraf import iraf

try:
    from cStringIO import StringIO
except ImportError:
    from io.StringIO import StringIO

INPUT_DATA = os.path.join(DATA_DIR, 'pset_msstat_input.fits')


@pytest.fixture(scope='function')
def _iraf_init():
    """Initialize common IRAF tasks
    """
    if not HAS_IRAF:
        return

    if not os.path.exists('login.cl'):
        subprocess.check_call('mkiraf -f xterm'.split())

    # imports & package loading
    iraf.stsdas(_doprint=0)
    iraf.imgtools(_doprint=0)
    iraf.mstools(_doprint=0)

    # reset PSET egstp's values
    _unlearn_egstp(iraf.egstp)


def _unlearn_egstp(egstp_obj):
    """Reset PSET egstp's values
    """
    egstp_obj.unlearn()
    egstp_obj.lParam()
    assert egstp_obj.npix == 0,  str(egstp_obj.npix)
    assert egstp_obj.min == 0.0, str(egstp_obj.min)
    assert egstp_obj.max == 0.0, str(egstp_obj.max)
    assert egstp_obj.sum == 0.0, str(egstp_obj.sum)


def assertApproxEqual(afloat, bfloat, tolerance=1.0e-12):
    if math.fabs(bfloat) > tolerance:
        ratiodiff = math.fabs(1.0 - math.fabs(afloat/(1.0*bfloat)))
        assert ratiodiff < tolerance, \
            '{} != {}, radiodiff = {}'.format(
                    afloat, bfloat, math.fabs(ratiodiff))
    else:
        diff = math.fabs(afloat - bfloat)
        assert diff < tolerance, \
            '{} != {}, diff = {}'.format(afloat, bfloat, math.fabs.diff)


@pytest.mark.skipif(not HAS_IRAF, reason='Need IRAF to run')
def test_pset_msstatis_science_array(_iraf_init):
    """Expect decent data
    """
    # Run msstat, which sets egstp values.  Test PSET par passing to task
    # command function as a task top-level par passing msstat.nsstatpar.arrays
    # and msstat.nsstatpar.clarray, as if they were just msstat pars...
    #     arrays='science' (check "science" arrays only)
    #    clarray='science' (return data to egstp from final "error" array)
    # So, expect vals from second (final) science array.

    iraf.msstatis(INPUT_DATA, arrays='science', clarray='science')
    iraf.egstp.lParam()

    assert iraf.egstp.npix == 277704, str(iraf.egstp.npix)
    assertApproxEqual(iraf.egstp.min, 1116.0)
    assertApproxEqual(iraf.egstp.max, 14022.0)
    assertApproxEqual(iraf.egstp.sum, 321415936.0)


@pytest.mark.skipif(not HAS_IRAF, reason='Need IRAF to run')
def test_pset_msstatis_zeroed_error_array(_iraf_init):
    """Expect zeros
    """
    # Run and get data for retval from error arrays (which are empty)
    #     arrays='science' (check "science" arrays only)
    #    clarray='error'   (return data to egstp from final "error" array)
    # so, since the 'error' arrays are empty (and unchecked), expect all zeroes
    iraf.msstatis(INPUT_DATA, arrays='science', clarray='error')
    iraf.egstp.lParam()

    assert iraf.egstp.npix == 0,  str(iraf.egstp.npix)
    assert iraf.egstp.min == 0.0, str(iraf.egstp.min)
    assert iraf.egstp.max == 0.0, str(iraf.egstp.max)
    assert iraf.egstp.sum == 0.0, str(iraf.egstp.sum)


@pytest.mark.skipif(not HAS_IRAF, reason='Need IRAF to run')
def test_pset_msstatis_min_match_task(_iraf_init):
    # Determine whether pyraf can use min-matching to resolve the task
    # (msstatis -> msstat)
    #
    # Note:
    # iraf.task does not raise an exception if it fails due to invalid input to
    # the function. We're scanning stdout/err here as a stop gap measure.

    stdout, stderr = StringIO(), StringIO()
    iraf.msstat(INPUT_DATA, arrays='science', clarray='science',
                StdoutAppend=stdout, StderrAppend=stderr)

    assert "ERROR" not in stdout.getvalue()
    assert not stderr.getvalue()


@pytest.mark.skipif(not HAS_IRAF, reason='Need IRAF to run')
def test_pset_msstatis_191():
    """Expect egstp to be properly cleared and used again
    """
    # Regression test to make sure a task can be sent an unadorned PSET
    # par as a regular function argument (without scope/PSET name given).
    # This regression-tests #191.

    # repeat first call to msstat, verify correct results and that we did
    # not hit anything which exists due to previous calls
    iraf.msstat(INPUT_DATA, arrays='science', clarray='science')
    iraf.egstp.lParam()

    assert iraf.egstp.npix == 277704, str(iraf.egstp.npix)
    assertApproxEqual(iraf.egstp.min, 1116.0)
    assertApproxEqual(iraf.egstp.max, 14022.0)
    assertApproxEqual(iraf.egstp.sum, 321415936.0)

    _unlearn_egstp(iraf.egstp)
    iraf.msstatis(INPUT_DATA, arrays='science', clarray='error')
    iraf.egstp.lParam()

    assert iraf.egstp.npix == 0,  str(iraf.egstp.npix)
    assert iraf.egstp.min == 0.0, str(iraf.egstp.min)
    assert iraf.egstp.max == 0.0, str(iraf.egstp.max)
    assert iraf.egstp.sum == 0.0, str(iraf.egstp.sum)

    _unlearn_egstp(iraf.egstp)
    iraf.msstat(INPUT_DATA, arrays='science', clarray='science')
    iraf.egstp.lParam()

    assert iraf.egstp.npix == 277704, str(iraf.egstp.npix)
    assertApproxEqual(iraf.egstp.min, 1116.0)
    assertApproxEqual(iraf.egstp.max, 14022.0)
    assertApproxEqual(iraf.egstp.sum, 321415936.0)


def test_pset_msstat_save_data():
    """Expect a task can save data into a PSET
    """
    # run msstat, which sets egstp values
    # check PSET egstp's values
    iraf.msstatis('dev$pix')
    iraf.egstp.lParam()
    assert iraf.egstp.npix == 262144, str(iraf.egstp.npix)
    assert iraf.egstp.min == -1.0, str(iraf.egstp.min)
    assert iraf.egstp.max == 19936.0, str(iraf.egstp.max)
    assert iraf.egstp.sum == 28394234.0, str(iraf.egstp.sum)

    # reset PSET egstp's values
    _unlearn_egstp(iraf.egstp)
    iraf.egstp.lParam()
    assert iraf.egstp.npix == 0, str(iraf.egstp.npix)
    assert iraf.egstp.min == 0.0, str(iraf.egstp.min)
    assert iraf.egstp.max == 0.0, str(iraf.egstp.max)
    assert iraf.egstp.sum == 0.0, str(iraf.egstp.sum)

    # run msstat again
    iraf.msstatis('dev$pix')

    # recheck PSET egstp's values
    iraf.egstp.lParam()
    assert iraf.egstp.npix == 262144, str(iraf.egstp.npix)
    assert iraf.egstp.min == -1.0, str(iraf.egstp.min)
    assert iraf.egstp.max == 19936.0, str(iraf.egstp.max)
    assert iraf.egstp.sum == 28394234.0, str(iraf.egstp.sum)
