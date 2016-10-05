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

def _env_logic(binmeta):
    gal_bgg = binmeta.metadata['gal bgg']
    gal_env = int(binmeta.metadata['gal env'])
    gal_mhalo = float(binmeta.metadata['gal mhalo'])
    if gal_bgg == 'True' and gal_env > 1:
        env = 'BGG'
    elif gal_bgg == 'False' and gal_env > 1:
        env = 'Satellite'
    elif gal_env == 1:
        env = 'Isolated'
    else:
        msg = ('unable to determine env '
               '(gal bgg = {0}; gal env = {1}; gal mhalo = {2})'
               ''.format(gal_bgg, gal_env, gal_mhalo))
        raise RuntimeError(msg)
    return env

def writemeta(output, bininfo_path, temps1_path, temps2_path, s2params_path,
              moments_path, rprofiles_path):
    keywidth = 8

    binmeta = header(bininfo_path)
    bininfo = np.genfromtxt(bininfo_path,names=True,skip_header=1)
    fullmoments = _readTempsMoments(temps1_path), _readTempsMoments(temps2_path)
    moments = np.genfromtxt(moments_path,names=True,skip_header=1)
    rmeta = header(rprofiles_path)

    fullbin_radius = {'f2': _read_s2_params(s2params_path),
                      'f1': np.nanmax(bininfo['rmax'])}

    junkbincount = int(rmeta.metadata['junk bins'])
    if junkbincount > 0:
        bininfo = bininfo[:-junkbincount]
        moments = moments[:-junkbincount]


    # Basic parameters
    output.write('#\n# Basic parameters\n#\n')
    items = OrderedDict()
    items['date'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    items['ra'] = binmeta.metadata['gal ra']
    items['dec'] = binmeta.metadata['gal dec']
    items['d'] = binmeta.metadata['gal d']
    items['mk'] = binmeta.metadata['gal mk']
    items['re'] = binmeta.metadata['gal re']
    items['eps'] = 1.0 - float(binmeta.metadata['gal ba'])
    items['pa'] = binmeta.metadata['gal pa']
    items['pakin'] = binmeta.metadata['gal pa']
    items['rmax'] = (np.nanmax(bininfo['rmax'])
                     / float(binmeta.metadata['gal re']))
    items['env'] = _env_logic(binmeta)
    items['envN'] = binmeta.metadata['gal env']
    output.write('\n'.join('{1:>{0}}: {2}'.format(keywidth, k, v)
                           for k, v in items.iteritems()))


    # Full galaxy spectrum parameters
    output.write('\n#\n# Full galaxy spectrum parameters\n#\n')
    items = OrderedDict()
    for i, f in enumerate(['f1', 'f2']):
        items['{0}rad'.format(f)] = fullbin_radius[f]
        for j, moment in enumerate(['v', 'sig', 'h3', 'h4', 'h5', 'h6']):
            items['{0}{1}'.format(f, moment)] = fullmoments[i][j]
    output.write('\n'.join('{1:>{0}}: {2}'.format(keywidth, k, v)
                           for k, v in items.iteritems()))

    # Averages over galaxy (within effective radius; flux-weighted)
    output.write('\n#\n# Averages over galaxy\n#\n')
    items = OrderedDict()
    items['sigc'] = moments['sigma'][0]
    items.update(get_re_averages(moments,bininfo,binmeta.metadata['gal re']))
    items['lam'] = rmeta.metadata['lambda re']
    output.write('\n'.join('{1:>{0}}: {2}'.format(keywidth, k, v)
                           for k, v in items.iteritems()))

    # Best-fit parameters
    output.write('\n#\n# Best-fit parameters\n#\n')
    items = OrderedDict()
    items.update(get_sigfits(moments,bininfo,binmeta.metadata['gal d']))
    items['h3vgrad'] = rmeta.metadata['h3 slope']
    items['h3vgrade'] = rmeta.metadata['h3 slope err']
    items['h3vint'] = rmeta.metadata['h3 intercept']
    items['h3vinte'] = rmeta.metadata['h3 intercept err']
    items.update(get_h4fits(moments,bininfo,binmeta.metadata['gal d']))

    width = max(len(str(k)) for k in items.keys())
    output.write('\n'.join('{1:>{0}}: {2}'.format(width, k, v)
                           for k, v in items.iteritems()))
