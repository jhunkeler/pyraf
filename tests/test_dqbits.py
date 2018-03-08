import os
import pytest

os.environ['PYRAF_NO_DISPLAY'] = '1'
from .utils import HAS_IRAF, DATA_DIR

if HAS_IRAF:
    from pyraf import iraf

INPUT_DATA = os.path.join(DATA_DIR, 'dqbits_input.fits')


@pytest.fixture
def _data(tmpdir):
    inputs = dict(
        input1 = str(tmpdir.join('im1.fits')),
        input2 = str(tmpdir.join('im2.fits')),
        output = str(tmpdir.join('out.fits'))
    )
    return inputs


@pytest.fixture
def _iraf_init(_data):
    # imports & package loading
    iraf.stsdas(_doprint=0)
    iraf.imgtools(_doprint=0)
    iraf.artdata(_doprint=0)
    iraf.mstools(_doprint=0)

    # create two data files as input (dont care if appropriate to mscombine)
    input_copy = 'copy_' + INPUT_DATA
    iraf.imcopy('dev$pix', _data['input1'])
    iraf.imcopy('dev$pix', _data['input2'])


def check_all_dqbits(the_dqbits_obj, valtup):
    """ Convenience method to check the 16 bitN values of dqbits """
    # converts to iraf yes and no's
    yes_no_map = { True: "iraf.yes", False: "iraf.no" }

    # check each one
    for i in range(16):
        expect_is_true = 'the_dqbits_obj.bit{} == {}'.format(i+1, yes_no_map[bool(valtup[i])])
        result = eval(expect_is_true)
        msg = "Expected this to be True: {}".format(expect_is_true)
        msg = msg.replace('the_dqbits_obj','dqbits')
        assert result, msg


def test_dqbits_mscombine(_iraf_init, _data, tmpdir):
    """Expect dqbits unaltered after combining data
    """
    # reset PSET dqbits' values
    iraf.dqbits.unlearn()
    check_all_dqbits(iraf.dqbits, (0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0) )
    iraf.dqbits.lParam()

    # now set PSET dqbits' values to a non-default set
    iraf.dqbits.bit2 = iraf.dqbits.bit4 = iraf.dqbits.bit6 = iraf.dqbits.bit8 = iraf.yes
    check_all_dqbits(iraf.dqbits, (0,1,0,1,0,1,0,1,0,0,0,0,0,0,0,0) )
    iraf.dqbits.lParam()

    # run mscombine to see what is does with the dqbit pars (shouldn't alter)
    inputs = ','.join([_data['input1'], _data['input2']])
    output = _data['output']
    iraf.mscombine(inputs, output)

    # now, check the PSET - should be unaltered (fixed by #207)
    iraf.dqbits.lParam()
    check_all_dqbits(iraf.dqbits, (0,1,0,1,0,1,0,1,0,0,0,0,0,0,0,0) )
