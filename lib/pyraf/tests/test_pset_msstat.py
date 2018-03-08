#!/usr/bin/env python
#
from __future__ import print_function

import math
import os
import pytest
import shutil
import subprocess
import sys

try:
    from cStringIO import StringIO
except ImportError:
    from io.StringIO import StringIO

# first turn off display
os.environ['PYRAF_NO_DISPLAY'] = '1'

from pyraf import iraf



@pytest.fixture(scope='function')
def _iraf_init():
    subprocess.check_call('mkiraf -f xterm'.split())

    # imports & package loading
    iraf.stsdas(_doprint=0)
    iraf.imgtools(_doprint=0)
    iraf.mstools(_doprint=0)

    # reset PSET egstp's values
    _unlearn_egstp(iraf.egstp)


def _unlearn_egstp(egstp_obj):
    # reset PSET egstp's values
    verbose = 0
    egstp_obj.unlearn()
    egstp_obj.lParam(verbose=0)
    assert egstp_obj.npix == 0,  str(egstp_obj.npix)
    assert egstp_obj.min == 0.0, str(egstp_obj.min)
    assert egstp_obj.max == 0.0, str(egstp_obj.max)
    assert egstp_obj.sum == 0.0, str(egstp_obj.sum)


def assertApproxEqual(afloat, bfloat, tolerance=1.0e-12):
    if math.fabs(bfloat) > tolerance:
        ratiodiff = math.fabs(1.0 - math.fabs(afloat/(1.0*bfloat)))
        assert ratiodiff < tolerance, str(afloat)+' != '+str(bfloat)+', ratiodiff = '+str(math.fabs(ratiodiff))
    else:
        diff = math.fabs(afloat - bfloat)
        assert diff < tolerance, str(afloat)+' != '+str(bfloat)+', diff = '+str(math.fabs(diff))


def test_pset_msstatis_science_array(_iraf_init):
    # Run msstat, which sets egstp values.  Test PSET par passing to task
    # command function as a task top-level par passing msstat.nsstatpar.arrays
    # and msstat.nsstatpar.clarray, as if they were just msstat pars...
    #     arrays='science' (check "science" arrays only)
    #    clarray='science' (return data to egstp from final "error" array)
    # So, expect vals from second (final) science array.

    iraf.msstatis('data/pset_msstat_input.fits', arrays='science', clarray='science')
    # TODO: No exception raised when task fails. Why?

    print("\nExpect decent data:")
    iraf.egstp.lParam()
    assert iraf.egstp.npix == 277704, str(iraf.egstp.npix)
    assertApproxEqual(iraf.egstp.min, 1116.0)
    assertApproxEqual(iraf.egstp.max, 14022.0)
    assertApproxEqual(iraf.egstp.sum, 321415936.0)


def test_pset_msstatis_zeroed_error_array(_iraf_init):
    # Run and get data for retval from error arrays (which are empty)
    #     arrays='science' (check "science" arrays only)
    #    clarray='error'   (return data to egstp from final "error" array)
    # so, since the 'error' arrays are empty (and unchecked), expect all zeroes
    iraf.msstatis('data/pset_msstat_input.fits', arrays='science', clarray='error')
    print("\nExpect zeroes:")
    iraf.egstp.lParam()
    assert iraf.egstp.npix == 0,  str(iraf.egstp.npix)
    assert iraf.egstp.min == 0.0, str(iraf.egstp.min)
    assert iraf.egstp.max == 0.0, str(iraf.egstp.max)
    assert iraf.egstp.sum == 0.0, str(iraf.egstp.sum)


def test_pset_msstatis_min_match_task(_iraf_init):
    # Determine whether pyraf can use min-matching to resolve the task
    # msstatis -> msstat
    iraf.msstat('data/pset_msstat_input.fits', arrays='science', clarray='science')


def test_pset_msstatis_191():
    # Regression test to make sure a task can be sent an unadorned PSET
    # par as a regular function argument (without scope/PSET name given).
    # This regression-tests #191.

    # repeat first call to msstat, verify correct results and that we did
    # not hit anything which exists due to previous calls
    iraf.msstat('data/pset_msstat_input.fits', arrays='science', clarray='science')
    iraf.egstp.lParam()
    assert iraf.egstp.npix == 277704, str(iraf.egstp.npix)
    assertApproxEqual(iraf.egstp.min, 1116.0)
    assertApproxEqual(iraf.egstp.max, 14022.0)
    assertApproxEqual(iraf.egstp.sum, 321415936.0)

    _unlearn_egstp(iraf.egstp)
    iraf.msstatis('data/pset_msstat_input.fits', arrays='science', clarray='error')
    iraf.egstp.lParam()
    assert iraf.egstp.npix == 0,  str(iraf.egstp.npix)
    assert iraf.egstp.min == 0.0, str(iraf.egstp.min)
    assert iraf.egstp.max == 0.0, str(iraf.egstp.max)
    assert iraf.egstp.sum == 0.0, str(iraf.egstp.sum)

    _unlearn_egstp(iraf.egstp)
    iraf.msstat('data/pset_msstat_input.fits', arrays='science', clarray='science')
    iraf.egstp.lParam()
    assert iraf.egstp.npix == 277704, str(iraf.egstp.npix)
    assertApproxEqual(iraf.egstp.min, 1116.0)
    assertApproxEqual(iraf.egstp.max, 14022.0)
    assertApproxEqual(iraf.egstp.sum, 321415936.0)
