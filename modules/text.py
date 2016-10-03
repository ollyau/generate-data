import os
import re

import numpy as np

from utils import header

def _getheaderfmt(i, fmt):
    r = re.compile(r'^%?(\d+)(?:\.(\d+))?([A-Za-z])$')
    m = r.search(fmt)
    if not m:
        raise ValueError('input {0} does not appear to be a format string'.format(fmt))
    val = m.group(1) if i > 0 else int(m.group(1)) - 2
    return '{{{0}:>{1}}}'.format(i, val)

def joindata(bininfopath, momentspath, rprofilespath, outputPath):
    columns = [
        ('bin', '%5d'),
        ('nf', '%4d'),
        ('an', '%3d'),
        ('flux', '%10.1f'),
        ('r', '%6.2f'),
        ('th', '%7.2f'),
        ('V', '%8.2f'),
        ('Verr', '%7.2f'),
        ('sig', '%6.2f'),
        ('sigerr', '%6.2f'),
        ('h3', '%7.4f'),
        ('h3err', '%6.4f'),
        ('h4', '%7.4f'),
        ('h4err', '%6.4f'),
        ('h5', '%7.4f'),
        ('h5err', '%6.4f'),
        ('h6', '%7.4f'),
        ('h6err', '%6.4f')
        ]

    cols, fmts = zip(*columns)

    bininfo = np.genfromtxt(
        bininfopath,
        dtype={
            'names':['binid', 'nfibers', 'flux', 'x', 'y', 'r', 'th', 'rmin', 'rmax', 'thmin', 'thmax'],
            'formats':2 * ['i4'] + 9 * ['f8']
            })

    moments = np.genfromtxt(
        momentspath,
        dtype={
            'names':['bin', 'V', 'sigma', 'h3', 'h4', 'h5', 'h6', 'Verr', 'sigmaerr', 'h3err', 'h4err', 'h5err', 'h6err'],
            'formats':['i4'] + 12 * ['f8']
            })

    rprofiles = np.genfromtxt(rprofilespath,dtype=None,names=True,skip_header=1)
        
    annuli = np.searchsorted(rprofiles['r_en'],bininfo['r'])
    r_check = np.zeros(len(rprofiles))
    for i in range(max(annuli)+1):
        ii = (annuli==i)
        lum = bininfo['nfibers'][ii]*bininfo['flux'][ii]
        r_check[i] = np.average(bininfo['r'][ii],weights=lum)
    if not all(np.isclose(r_check,rprofiles['r'])):
        raise Exception('WARNING, YOUR ANNULI ARE WRONG')
    
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

    junkbins = int(header(rprofilespath).metadata['junk bins'])
    if junkbins > 0:
        bincount = len(newdata)
        newdata = np.delete(newdata, range(bincount - junkbins, bincount), 0)

    v = newdata[:, 6]
    if np.any(v > 9999) or np.any(v < -9999):
        print('warning: value for V exceeds 9999 or is below -9999')
    sigma = newdata[:, 8]
    if np.any(sigma > 999) or np.any(sigma < 0):
        print('warning: value for sigma exceeds 999 or is negative')

    newheader = ' '.join([_getheaderfmt(i, fmt) for i, fmt in enumerate(fmts)])
    np.savetxt(outputPath, newdata, header=newheader.format(*cols), fmt=fmts)

def test():
    dataDirectory = r'..\kinematics_paperversion\kinematics_paperversion\more_files'
    outputDirectory = r'..\Output\batch2'
    files = os.listdir(dataDirectory)

    search = re.compile(r'^((?:NGC|UGC)\d+).+\.txt$').search
    galaxies = sorted(set(m.group(1) for m in (search(g) for g in files) if m))

    for gal in galaxies:
        thing1 = os.path.join(dataDirectory, gal + '-s2-folded-bininfo.txt')
        thing2 = os.path.join(dataDirectory, gal + '-s3-B-folded-moments.txt')
        thing3 = os.path.join(dataDirectory, gal + '-s4-folded-rprofiles.txt')
        joindata(thing1, thing2, thing3, os.path.join(outputDirectory, gal + '-folded-data.txt'))

if __name__ == '__main__':
    test()
