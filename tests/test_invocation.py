from .utils import HAS_IRAF, HAS_PYRAF_EXEC
import os
import pytest
import pyraf
import re
import shutil
import subprocess
import sys
from distutils.spawn import find_executable


class PyrafEx:
    def __init__(self):
        self.code = 0
        self.stdout = None
        self.stderr = None

    def run(self, args):
        if isinstance(args, str):
            args = args.split()

        cmd = ['pyraf', '-x', '-s']
        cmd += args
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.stdout, self.stderr = proc.communicate()

        if sys.hexversion >= 0x0300000F0:
            self.stdout = self.stdout.decode('ascii')
            self.stderr = self.stderr.decode('ascii')

        self.code = proc.returncode
        return self


@pytest.fixture
def _with_pyraf(tmpdir):
    return PyrafEx()


@pytest.mark.skipif(not HAS_PYRAF_EXEC, reason='PyRAF must be installed to run')
@pytest.mark.parametrize('test_input', [
    ('--version'),
    ('-V'),
])
def test_invoke_version(_with_pyraf, test_input):
    result = _with_pyraf.run(test_input)
    assert not result.code
    assert pyraf.__version__ in result.stdout


@pytest.mark.skipif(not HAS_PYRAF_EXEC, reason='PyRAF must be installed to run')
@pytest.mark.skipif(not HAS_IRAF, reason='PyRAF must be installed to run')
@pytest.mark.parametrize('test_input,expected', [
    (('-c', 'print(1)'), '1'),
    (('-c', 'print(1 + 2)'), '3'),
    (('-c', 'print(10 / 2)'), '5'),
    (('-c', 'print(3 * 2.5)'), '7'),
    (('-c', 'imhead("dev$pix")'), 'dev$pix[512,512][short]: m51  B  600s'),
    (('-c', 'unlearn imcoords'), ''),
    (('-c', 'bye'), ''),
])
def test_invoke_command(_with_pyraf, test_input, expected):
    result = _with_pyraf.run(test_input)
    assert result.stdout.startswith(expected)


