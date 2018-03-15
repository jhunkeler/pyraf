"""These were tests under core/graphics_checks in pandokia."""
import os
import sys

import pytest
import six

from .utils import IS_PY2, HAS_IRAF

if HAS_IRAF:
    from pyraf import iraf
    from pyraf import gki
    from pyraf import wutil

REF = {}


def setup_module():
    global REF

    # first turn off display
    os.environ['PYRAF_NO_DISPLAY'] = '1'

    # EXPECTED RESULTS
    REF[('2', 'linux')] = """python ver = 2.7
platform = linux2
PY3K = False
c.OF_GRAPHICS = False
/dev/console owner = <skipped>
tkinter use unattempted.
"""
    REF[('2', 'darwin')] = REF[('2', 'linux')].replace('linux2', 'darwin')

    REF[('3', 'linux')] = """python ver = 3.5
platform = linux
PY3K = True
c.OF_GRAPHICS = False
/dev/console owner = <skipped>
tkinter use unattempted.
"""
    REF[('3', 'darwin')] = REF[('3', 'linux')].replace('linux', 'darwin')


@pytest.mark.skipif(not HAS_IRAF, reason='Need IRAF to run')
def test_dumpspecs():
    # get dumpspecs output
    out_f = six.StringIO()
    wutil.dumpspecs(outstream=out_f, skip_volatiles=True)
    out_str = out_f.getvalue()
    out_f.close()

    # modify out_str to remove a path that will always be changing
    out_str = '\n'.join([l for l in out_str.split('\n')
                         if 'python exec =' not in l])
    # modify out_str to handle old versions which printed Tkinter as camel-case
    out_str = out_str.replace('Tkinter', 'tkinter')

    # verify it (is version dependent)
    key = ('2' if IS_PY2 else '3', sys.platform.replace('2', ''))
    expected = REF[key]
    assert expected.strip() == out_str.strip(), \
        'Unexpected output from wutil.dumpspecs: {}'.format(out_str)


@pytest.mark.skipif(not HAS_IRAF, reason='Need IRAF to run')
def test_gkidecode(tmpdir):
    iraf.plot(_doprint=0)
    prow_stdout = str(tmpdir.join('test_prow_256.gki'))
    gki_stdout = str(tmpdir.join('gkidecode_stdout.txt'))
    gki_stderr = str(tmpdir.join('gkidecode_stderr.txt'))

    iraf.prow("dev$pix", row=256, StdoutG=prow_stdout)
    iraf.gkidecode(prow_stdout, Stdout=gki_stdout, Stderr=gki_stderr)
    assert 'close_workstation' in open(gki_stdout).readlines()[-1]
    assert not open(gki_stderr).readlines()


@pytest.mark.parametrize('test_input', [
    'psdump',
    'psi_land',
])
def test_gki_postscript_in_graphcap(test_input):
   """ Verify that the graphcap file supports psdump and psi_land """
   gc = gki.getGraphcap()
   assert gc, "default graphcap not found"
   assert test_input in gc, \
           "default graphcap does not support {}".format(test_input)
   device = gc[test_input]
   assert device.devname == test_input, \
           "Invalid graphcap device for {}".format(test_input)


def test_gki_opcodes():
   """ Simple aliveness test for the opcode2name dict """
   for opc in gki.GKI_ILLEGAL_LIST:
      assert gki.opcode2name[opc] == 'gki_unknown'


def test_gki_control_codes():
   """ Simple aliveness test for the control2name dict """
   for ctl in gki.GKI_ILLEGAL_LIST:
      assert gki.control2name[ctl] == 'control_unknown'
