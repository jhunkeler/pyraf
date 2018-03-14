"""These were tests under core/irafparlist and core/subproc in pandokia."""
from __future__ import absolute_import, division

import pytest
import time

from .utils import diff_outputs, HAS_IRAF

if HAS_IRAF:
    from pyraf.irafpar import IrafParList
    from pyraf.subproc import Subprocess, SubprocessError
    from stsci.tools import basicpar


@pytest.fixture
def _proc():
    return Subprocess('cat', expire_noisily=0)


#@pytest.mark.skipif(not HAS_IRAF, reason='Need IRAF to run')
#def test_irafparlist(tmpdir):
#    outfile = str(tmpdir.join('output.txt'))
#
#    with open(outfile, 'w') as f:
#        irafpar.test_IrafParList(f)
#
#    diff_outputs(outfile, 'data/core_irafparlist_output.ref')


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


@pytest.fixture
def _ipl_defaults(tmpdir):
    defaults = dict(
        name='bobs_pizza',
        filename=str(tmpdir.join('bobs_pizza.par'))
    )
    return defaults


@pytest.fixture
def _ipl(_ipl_defaults):
    """An IrafParList object
    """
    return IrafParList(_ipl_defaults['name'], _ipl_defaults['filename'])


@pytest.mark.xfail(reason="BUG: Returns file path instead of name")
def test_irafparlist_getName(_ipl, _ipl_defaults):
    assert _ipl.getName() == _ipl_defaults['name']


def test_irafparlist_getFilename(_ipl, _ipl_defaults):
    assert _ipl.getFilename() == _ipl_defaults['filename']


def test_irafparlist_getPkgname(_ipl, _ipl_defaults):
    assert not _ipl.getPkgname()


def test_irafparlist_hasPar_defaults(_ipl, _ipl_defaults):
    assert _ipl.hasPar('$nargs')
    assert _ipl.hasPar('mode')
    assert len(_ipl) == 2


def test_irafparlist_addParam_quick(_ipl):
    par = basicpar.parFactory(
          ('caller', 's', 'a', 'Ima Hungry', '', None, 'person calling Bobs'),
          True)
    _ipl.addParam(par)
    assert len(_ipl) == 3
    assert _ipl.getAllMatches('') == ['caller', '$nargs', 'mode']


def meh_IrafParList():
    """ Test the IrafParList class """
    # let's add some pars
    par1 = basicpar.parFactory( \
           ('caller','s','a','Ima Hungry','',None,'person calling Bobs'), True)
    x = par1.dpar().strip()
    assert x == "caller = 'Ima Hungry'", "par1 is off: "+str(x)
    par2 = basicpar.parFactory( \
           ('diameter','i','a','12','',None,'pizza size'), True)
    x = par2.dpar().strip()
    assert x == "diameter = 12", "par2 is off: "+str(x)
    par3 = basicpar.parFactory( \
           ('pi','r','a','3.14159','',None,'Bob makes circles!'), True)
    x = par3.dpar().strip()
    assert x == "pi = 3.14159", "par3 is off: "+str(x)
    par4 = basicpar.parFactory( \
           ('delivery','b','a','yes','',None,'delivery? (or pickup)'), True)
    x = par4.dpar().strip()
    assert x == "delivery = yes", "par4 is off: "+str(x)
    par5 = basicpar.parFactory( \
           ('topping','s','a','peps','|toms|peps|olives',None,'the choices'), True)
    x = par5.dpar().strip()
    assert x == "topping = 'peps'", "par5 is off: "+str(x)

    pl.addParam(par1)
    assert len(pl) == 3, "Unexpected length: "+str(len(pl))
    pl.addParam(par2)
    pl.addParam(par3)
    pl.addParam(par4)
    pl.addParam(par5)
    assert len(pl) == 7, "Unexpected length: "+str(len(pl))

    # now we have a decent IrafParList to play with - test some
    fout.write("lParam should show 6 actual pars (our 5 + mode)\n"+\
               pl.lParamStr()+'\n')
    assert pl.__doc__ == 'List of Iraf parameters',"__doc__ = "+str(pl.__doc__)
    x = sorted(pl.getAllMatches(''))
    assert x==['$nargs','caller','delivery','diameter','mode','pi','topping'],\
           "Unexpected all: "+str(x)
    x = sorted(pl.getAllMatches('d'))
    assert x == ['delivery','diameter'], "Unexpected d's: "+str(x)
    x = sorted(pl.getAllMatches('jojo'))
    assert x == [], "Unexpected empty list: "+str(x)
    x = pl.getParDict()
    assert 'caller' in x, "Bad dict? "+str(x)
    x = pl.getParList()
    assert par1 in x, "Bad list? "+str(x)
    assert pl.hasPar('topping'), "hasPar call failed"
    # change a par val
    pl.setParam('topping','olives') # should be no prob
    assert 'olives' == pl.getParDict()['topping'].value, \
           "Topping error: "+str(pl.getParDict()['topping'].value)
    try:
       # the following setParam should fail - not in choice list
       pl.setParam('topping','peanutbutter') # oh the horror
       raise RuntimeError("The bad setParam didn't fail?")
    except ValueError:
       pass

    # Now try some direct access (also tests IrafPar basics)
    assert pl.caller == "Ima Hungry", 'Ima? '+pl.getParDict()['caller'].value
    pl.pi = 42
    assert pl.pi == 42.0, "pl.pi not 42, ==> "+str(pl.pi)
    try:
       pl.pi = 'strings are not allowed' # should throw
       raise RuntimeError("The bad pi assign didn't fail?")
    except ValueError:
       pass
    pl.diameter = '9.7' # ok, string to float to int
    assert pl.diameter == 9, "pl.diameter?, ==> "+str(pl.diameter)
    try:
       pl.diameter = 'twelve' # fails, not parseable to an int
       raise RuntimeError("The bad diameter assign didn't fail?")
    except ValueError:
       pass
    assert pl.diameter == 9, "pl.diameter after?, ==> "+str(pl.diameter)
    pl.delivery = False # converts
    assert pl.delivery == no, "pl.delivery not no? "+str(pl.delivery)
    pl.delivery = 1 # converts
    assert pl.delivery == yes, "pl.delivery not yes? "+str(pl.delivery)
    pl.delivery = 'NO' # converts
    assert pl.delivery == no, "pl.delivery not NO? "+str(pl.delivery)
    try:
       pl.delivery = "maybe, if he's not being recalcitrant"
       raise RuntimeError("The bad delivery assign didn't fail?")
    except ValueError:
       pass
    try:
       pl.topping = 'peanutbutter' # try again
       raise RuntimeError("The bad topping assign didn't fail?")
    except ValueError:
       pass
    try:
       x = pl.pumpkin_pie
       raise RuntimeError("The pumpkin_pie access didn't fail?")
    except KeyError:
       pass
