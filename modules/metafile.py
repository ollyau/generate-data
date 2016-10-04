from collections import OrderedDict
import datetime
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

def writemeta(fbininfo, ftemps1, ftemps2, fs2params, fbinmoments, frprofiles, output):
    items = OrderedDict()

    bininfo = header(fbininfo)
    rprofiles = header(frprofiles)
    moments = _readTempsMoments(ftemps1), _readTempsMoments(ftemps2)
    fullbin_radius = _read_s2_params(fs2params)
    binmoments = np.genfromtxt(fbinmoments,names=True,skip_header=1)
    bindata = np.genfromtxt(fbininfo,names=True,skip_header=1)

    rmax = np.genfromtxt(fbininfo, usecols=8)
    junkbincount = int(rprofiles.metadata['junk bins'])

    gal_bgg = bininfo.metadata['gal bgg']
    gal_env = int(bininfo.metadata['gal env'])
    gal_mhalo = float(bininfo.metadata['gal mhalo'])
    if gal_bgg == 'True':
        env = 'BGG'
    elif gal_env > 1:
        env = 'Satellite'
    elif gal_env == 1:
        env = 'Isolated'
    else:
        raise RuntimeError('unable to determine env (gal bgg = {0}; gal env = {1}; gal mhalo = {2})'.format(gal_bgg, gal_env, gal_mhalo))

    # Basic parameters
    items['date'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    items['ra'] = bininfo.metadata['gal ra']
    items['dec'] = bininfo.metadata['gal dec']
    items['d'] = bininfo.metadata['gal d']
    items['mk'] = bininfo.metadata['gal mk']
    items['re'] = bininfo.metadata['gal re']
    items['eps'] = 1.0 - float(bininfo.metadata['gal ba'])
    items['pa'] = bininfo.metadata['gal pa']
    items['pakin'] = bininfo.metadata['gal pa']
    items['rmax'] = rmax[-1 - junkbincount] / float(bininfo.metadata['gal re']) # highest after throwing away junk bins
    items['env'] = env
    items['envN'] = bininfo.metadata['gal env']

    # Full galaxy spectrum parameters
    # f1rad is highest r (including junk bins)
    for i, gal in enumerate(['f1', 'f2']):
        items['{0}rad'.format(gal)] = rmax[-1] if i == 0 else fullbin_radius
        for j, moment in enumerate(['v', 'sig', 'h3', 'h4', 'h5', 'h6']):
            items['{0}{1}'.format(gal, moment)] = moments[i][j]

    # Averages over galaxy (within effective radius; flux-weighted)
    items['sigc'] = binmoments['sigma'][0]
    items.update(get_re_averages(binmoments,bindata,bininfo.metadata['gal re']))
    items['lam'] = rprofiles.metadata['lambda re']
    items['rot'] = 'Slow' if int(rprofiles.metadata['is slow']) == 1 else 'Fast' if float(rprofiles.metadata['lambda re']) > 0.2 else 'Unclassified'

    # Best-fit parameters
    items.update(get_sigfits(binmoments,bindata,bininfo.metadata['gal d']))
    items['h3vgrad'] = rprofiles.metadata['h3 slope']
    items['h3vgrade'] = rprofiles.metadata['h3 slope err']
    items['h3vint'] = rprofiles.metadata['h3 intercept']
    items['h3vinte'] = rprofiles.metadata['h3 intercept err']
    items.update(get_h4fits(binmoments,bindata,bininfo.metadata['gal d']))

    width = max(len(str(k)) for k in items.keys())
    output.write('\n'.join('{1:>{0}}: {2}'.format(width, k, v)
                           for k, v in items.iteritems()))
