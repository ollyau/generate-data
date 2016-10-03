import re
import numpy as np
from fitmoments import get_sigfits, get_h4fits
from annuli import get_re_averages
from utils import header, getstream

def _readTempsMoments(fname):
    moments = False
    stream, opened = getstream(fname)
    for line in stream:
        if moments == True:
            data = [float(x) for x in line[1:].split()]
            if opened:
                stream.close()
            if len(data) != 6:
                raise RuntimeError('expected 6 moments')
            return data
        if line == '# The best-fit moments are:\n':
            moments = True

def _read_s2_params(fname):
    stream, opened = getstream(fname)
    search = re.compile(r'^fullbin_radius\s+(-?\d+(\.\d*)?)').search
    fullbin_radius = next(m for m in (search(s) for s in stream) if m)
    if not fullbin_radius:
        if opened:
            stream.close()
        raise RuntimeError('unable to locate fullbin_radius')
    if opened:
        stream.close()
    return float(fullbin_radius.group(1))

def writemeta(fbininfo, ftemps1, ftemps2, fs2params, fbinmoments, output):
    items = {}

    bininfo = header(fbininfo)
    moments = _readTempsMoments(ftemps1), _readTempsMoments(ftemps2)
    fullbin_radius = _read_s2_params(fs2params)
    binmoments = np.genfromtxt(fbinmoments,names=True,skip_header=1)
    bindata = np.genfromtxt(fbininfo,names=True,skip_header=1)

    rmax = np.genfromtxt(fbininfo, usecols=8)

    items['gal pa'] = bininfo.metadata['gal pa']
    items['temps2_radius'] = fullbin_radius
    items['temps1_radius'] = rmax[-1]

    for i, gal in enumerate(['gal1', 'gal2']):
        for j, moment in enumerate(['V', 'sigma', 'h3', 'h4', 'h5', 'h6']):
            items['{0}_{1}'.format(gal, moment)] = moments[i][j]

    items.update(get_sigfits(binmoments,bindata,bininfo.metadata['gal d']))
    items.update(get_h4fits(binmoments,bindata,bininfo.metadata['gal d']))

    items.update(get_re_averages(binmoments,bindata,bininfo.metadata['gal re']))

    width = max(len(str(k)) for k in items.keys()) + 1
    if width < 22:
        width = 22
    output.write('\n'.join('# {1:>{0}}: {2}'.format(width, k, v) for k, v in sorted(items.iteritems())))

def test():
    with open(r'..\Output\test.txt', 'w') as output:
        writemeta(
            r'..\Data\kinematics_paperversion\kinematics_paperversion\more_files\NGC0057-s2-fibers-bininfo.txt',
            r'..\Data\kinematics_paperversion\kinematics_paperversion\more_files\NGC0057-s3-A-folded-temps-1.txt',
            r'..\Data\kinematics_paperversion\kinematics_paperversion\more_files\NGC0057-s3-A-folded-temps-2.txt',
            r'..\Data\kinematics_paperversion\kinematics_paperversion\more_files\NGC0057_s2_params.txt',
            output
            )

if __name__ == '__main__':
    test()
