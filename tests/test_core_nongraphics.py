"""These were tests under core/irafparlist and core/subproc in pandokia."""
from __future__ import absolute_import, division

import pytest
import time

from .utils import diff_outputs, HAS_IRAF

if HAS_IRAF:
    from pyraf import irafpar
    from pyraf.subproc import Subprocess, SubprocessError


@pytest.fixture
def _proc():
    return Subprocess('cat', expire_noisily=0)


@pytest.mark.skipif(not HAS_IRAF, reason='Need IRAF to run')
def test_irafparlist(tmpdir):
    outfile = str(tmpdir.join('output.txt'))

    with open(outfile, 'w') as f:
        irafpar.test_IrafParList(f)

    diff_outputs(outfile, 'data/core_irafparlist_output.ref')


@pytest.mark.xfail(reason="BUGGED")
def test_subproc_raise_on_bogus():
    """Raise on failure to execute process
    (It doesn't though...)
    """
    with pytest.raises(SubprocessError):
        proc = Subprocess('/', 1, expire_noisily=1)
        proc.wait(1)


def test_subproc_write_readline(_proc):
    """Buffer readback test; readline
    """
    _proc.write('test string one\n')
    _proc.write('test string two\n')
    time.sleep(0.01)

    assert _proc.readline() == 'test string one\n'
    assert _proc.readline() == 'test string two\n'


def test_subproc_write_readPendingChars(_proc):
    """Buffer readback test; readPendingChars
    """
    test_inputs = ('one', 'two', 'three')
    for test_input in test_inputs:
        _proc.write(test_input + '\n')
        time.sleep(0.01)

    expected = tuple(_proc.readPendingChars().splitlines())
    assert test_inputs == expected


def test_subproc_stop_resume(_proc):
    """Ensure we can stop and resume a process
    """
    assert _proc.stop(1)
    assert _proc.cont(1)


def test_subproc_stop_resume_write_read(_proc):
    """Ensure we can stop the process, write data to the pipe,
    resume, then read the buffered data back from the pipe.
    """
    assert _proc.stop(1)
    _proc.write('test string\n')
    assert not len(_proc.readPendingChars())
    assert _proc.cont(1)
    assert _proc.readline() == 'test string\n'


def test_subproc_kill_via_delete(_proc):
    """Kill the process by deleting the instance.
    We cannot assert anything, but an exception will bomb this out.
    """
    del _proc


def test_subproc_kill_via_die(_proc):
    """Kill the process the "right way."
    """
    assert _proc.pid is not None
    _proc.die()
    assert _proc.pid is None
