import os
from skyfield.api import load, load_file

from assay import assert_raises

def _data_path(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)

# Test file generated with:
# python -m jplephem excerpt 1969/07/29 1969/07/30 de441.bsp de441-1969.bsp

def test_multiple_non_overlapping_segments_per_target():
    ts = load.timescale()
    t = ts.utc(1969, 7, [28, 29, 30, 31])
    eph = load_file(_data_path('./de441-1969.bsp'))

    pluto = eph['pluto barycenter']
    assert type(pluto).__name__ == 'Stack'
    assert len(pluto.segments) == 2

    assert str(pluto.at(t).xyz) == (
        '[[-30.47352052 -30.47318972 -30.47285863 -30.47252727]\n'
        ' [ -0.96671442  -0.96985773  -0.97300104  -0.97614434]\n'
        ' [  8.87919555   8.87811509   8.87703455   8.87595392]] au'
    )

    # Does the Stack correctly offer its .ephemeris to apparent()?

    pluto.at(t).observe(pluto).apparent()

    # TODO: SSB.at(t).observe() fails the above test.

# Verify that ephemeris objects let their segments be edited.

def test_removing_segments_from_ephemeris():
    eph = load('de421.bsp')
    eph.segments = [s for s in eph.segments if s.target in (3, 4)]

    assert len(eph.segments) == 2
    assert 2 not in eph
    assert 3 in eph
    assert eph.codes == {0, 3, 4}
    assert eph.names() == {
        0: ['SOLAR_SYSTEM_BARYCENTER', 'SSB', 'SOLAR SYSTEM BARYCENTER'],
        3: ['EARTH_BARYCENTER', 'EMB', 'EARTH MOON BARYCENTER',
            'EARTH-MOON BARYCENTER', 'EARTH BARYCENTER'],
        4: ['MARS_BARYCENTER', 'MARS BARYCENTER'],
    }

    assert repr(eph) == "<SpiceKernel 'de421.bsp'>"
    assert str(eph) == """\
Segments from kernel file 'de421.bsp':
  JD 2414864.50 - JD 2471184.50  (1899-07-28 through 2053-10-08)
      0 -> 3    SOLAR SYSTEM BARYCENTER -> EARTH BARYCENTER
      0 -> 4    SOLAR SYSTEM BARYCENTER -> MARS BARYCENTER"""

    assert type(eph[4]).__name__ == 'ChebyshevPosition'
    with assert_raises(KeyError, 'is missing 5'):
        eph[5]

def test_adding_segments_to_ephemeris():
    eph = load('de405.bsp')
    eph.segments = [s for s in eph.segments if s.target == 3]

    eph2 = load('de421.bsp')
    eph.segments.extend((s for s in eph2.segments if s.target in (301, 399)))

    assert len(eph.segments) == 3
    assert 2 not in eph
    assert 3 in eph
    assert 301 in eph
    assert eph.codes == {0, 3, 301, 399}
    assert eph.names() == {
        0: ['SOLAR_SYSTEM_BARYCENTER', 'SSB', 'SOLAR SYSTEM BARYCENTER'],
        3: ['EARTH_BARYCENTER', 'EMB', 'EARTH MOON BARYCENTER',
            'EARTH-MOON BARYCENTER', 'EARTH BARYCENTER'],
        301: ['MOON'], 399: ['EARTH'],
    }

    assert repr(eph) == "<SpiceKernel 'de405.bsp' 'de421.bsp'>"
    assert str(eph) == """\
Segments from kernel file 'de405.bsp':
  JD 2305424.50 - JD 2525008.50  (1599-12-08 through 2201-02-19)
      0 -> 3    SOLAR SYSTEM BARYCENTER -> EARTH BARYCENTER
And from kernel file 'de421.bsp':
  JD 2414864.50 - JD 2471184.50  (1899-07-28 through 2053-10-08)
      3 -> 301  EARTH BARYCENTER -> MOON
      3 -> 399  EARTH BARYCENTER -> EARTH"""

    vs = eph[399]
    assert type(vs).__name__ == 'VectorSum'
    assert str(vs) == """\
Sum of 2 vectors:
 'de405.bsp' segment 0 SOLAR SYSTEM BARYCENTER -> 3 EARTH BARYCENTER
 'de421.bsp' segment 3 EARTH BARYCENTER -> 399 EARTH"""

    with assert_raises(KeyError):
        eph[4]

def test_ephemeris_lacking_segments_to_connect_to_barycenter():
    eph = load('de421.bsp')
    eph.segments = [s for s in eph.segments if s.target == 399]
    with assert_raises(KeyError, "Barycenter to the target 'Earth'"):
        eph['Earth']
