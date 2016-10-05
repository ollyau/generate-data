import os
import re

import numpy as np

from utils import header

def _getheaderfmt(i, fmt):
    r = re.compile(r'^%?(\d+)(?:\.(\d+))?([A-Za-z])$')
    m = r.search(fmt)
    if not m:
        msg = 'input {0} does not appear to be a format string'.format(fmt)
        raise ValueError(msg)
    val = m.group(1) if i > 0 else int(m.group(1)) - 2
    return '{{{0}:>{1}}}'.format(i, val)

def writetext(bininfopath, momentspath, rprofilespath, outputPath):
    columns = [
        ('bin', '%5d'),
        ('nf', '%4d'),
        ('ann', '%3d'),
        ('flux', '%10.1f'),
        ('r', '%6.2f'),
        ('th', '%7.2f'),
        ('V', '%8.2f'),
        ('Ve', '%7.2f'),
        ('sig', '%8.2f'),
        ('sige', '%6.2f'),
        ('h3', '%8.4f'),
        ('h3e', '%6.4f'),
        ('h4', '%7.4f'),
        ('h4e', '%6.4f'),
        ('h5', '%7.4f'),
        ('h5e', '%6.4f'),
        ('h6', '%7.4f'),
        ('h6e', '%6.4f')
        ]

    cols, fmts = zip(*columns)

    bininfo = np.genfromtxt(bininfopath,dtype=None,names=True,skip_header=1)
    moments = np.genfromtxt(momentspath,dtype=None,names=True,skip_header=1)
    rprofiles = np.genfromtxt(rprofilespath,dtype=None,names=True,skip_header=1)

    junkbins = int(header(rprofilespath).metadata['junk bins'])
    if junkbins > 0:
        bininfo = bininfo[:-junkbins]
        moments = moments[:-junkbins]

    annuli = np.searchsorted(rprofiles['r_en'],bininfo['r'])
    r_check = np.zeros(len(rprofiles))
    for i in range(max(annuli)+1):
        ii = (annuli==i)
        lum = bininfo['nfibers'][ii]*bininfo['flux'][ii]
        r_check[i] = np.average(bininfo['r'][ii],weights=lum)
    if not all(np.isclose(r_check,rprofiles['r'])):
        raise RuntimeError('WARNING, YOUR ANNULI ARE WRONG')

    newdata = np.column_stack((
        bininfo['binid'],
        bininfo['nfibers'],
        annuli,
        bininfo['flux'],
        bininfo['r'],
        bininfo['th'],
        moments['V'],
        moments['Verr'],
        moments['sigma'],
        moments['sigmaerr'],
        moments['h3'],
        moments['h3err'],
        moments['h4'],
        moments['h4err'],
        moments['h5'],
        moments['h5err'],
        moments['h6'],
        moments['h6err']
    ))

    v = newdata[:, 6]
    if np.any(v > 9999) or np.any(v < -9999):
        print('warning: value for V exceeds 9999 or is below -9999')
    sigma = newdata[:, 8]
    if np.any(sigma > 999) or np.any(sigma < 0):
        print('warning: value for sigma exceeds 999 or is negative')

    newheader = ' '.join([_getheaderfmt(i, fmt) for i, fmt in enumerate(fmts)])
    np.savetxt(outputPath, newdata, header=newheader.format(*cols), fmt=fmts)
