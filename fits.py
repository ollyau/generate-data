import numpy as np
from astropy.io import fits
from utils import header

def printhduinfo(fitsfile):
    fitsfile.info()
    for i, hdu in enumerate(fitsfile):
        name = (hdu.header['EXTNAME']
                if 'EXTNAME' in hdu.header.keys()
                else hdu.header['PRIMARY'] if 'PRIMARY' in hdu.header.keys()
                else 'unknown')
        print('HDU {0} {1} dimensions {2}'.format(i, name, hdu.data.shape))
        #header = hdu.header # header contains cards
        #cards = hdu.header.cards # cards contain key, val, comment (header metadata)
        #data = hdu.data # just some array of data, hopefully documented in header cards
        #dims = hdu.data.shape # dims of array since that's useful to know
        col1_width = max(len(str(val)) for val in hdu.header.keys()) + 4
        col2_width = max(len(str(val)) for val in hdu.header.values()) + 2
        for c in hdu.header.cards:
            print('{2:>{0}} {3:<{1}} {4}'.format(col1_width, col2_width, *c))

def createfits(fbinspectra, ffullgalaxy, fbininfo, fmoments, rprofiles, output):
    junkbins = int(header(rprofiles).metadata['junk bins'])

    # primary hdu (1): stack s2-folded-binspectra hdu 0 (spectra), 1 (noise), 3 (bad pixel flag), 4 (ir)
    # get wavelength data from s2-folded-binspectra hdu 2 (waves)
    binspectra = fits.open(fbinspectra)
    #printhduinfo(binspectra)

    # indices: data[i][j][k] where i, j, k are bin, column, and data
    # columns: 0 (spectra), 1 (noise), 2 (ir), 3 (bad pixel flag)
    result = np.stack((binspectra[0].data, binspectra[1].data, binspectra[4].data, binspectra[3].data), axis=1)

    bincount = len(result)
    hdu1data = result if junkbins == 0 else np.delete(result, range(bincount - junkbins, bincount), 0)

    binspectrawavespace = np.diff(np.log10(binspectra[2].data))
    if not np.allclose(binspectrawavespace, binspectrawavespace[0]):
        raise RuntimeError('wavelength spacing in s2-folded-binspectra is not consistent')

    hdu1header = fits.Header([
        fits.Card(keyword='PRIMARY', value='bin data'),
        fits.Card(keyword='WAVSTART', value=str(binspectra[2].data[0])),
        fits.Card(keyword='WAVEND', value=str(binspectra[2].data[-1])),
        fits.Card(keyword='WAVSPACE', value=str(binspectrawavespace[0])),
        ])

    # hdu 2: stack s2-folded-fullgalaxy.fits hdu 0 (spectra), 1 (noise), 3 (bad pixel flag), 4 (ir)
    # get wavelength data from s2-folded-fullgalaxy hdu 2 (waves) (should match binspectra)
    fullgalaxy = fits.open(ffullgalaxy)
    #printhduinfo(fullgalaxy)

    # indices: data[i][j][k] where i, j, k are bin, column, and data
    # columns: 0 (spectra), 1 (noise), 2 (ir), 3 (bad pixel flag)
    hdu2data = np.stack((fullgalaxy[0].data, fullgalaxy[1].data, fullgalaxy[4].data, fullgalaxy[3].data), axis=1)

    fullgalaxywavespace = np.diff(np.log10(fullgalaxy[2].data))
    if not np.allclose(fullgalaxywavespace, fullgalaxywavespace[0]):
        raise RuntimeError('s2-folded-binspectra does not have same wavelength spacing as s2-folded-fullgalaxy')

    hdu2header = fits.Header([
        fits.Card(keyword='WAVSTART', value=str(fullgalaxy[2].data[0])),
        fits.Card(keyword='WAVEND', value=str(fullgalaxy[2].data[-1])),
        fits.Card(keyword='WAVSPACE', value=str(fullgalaxywavespace[0])),
        ])

    # verify wavelength spacing
    if not np.allclose(binspectrawavespace, fullgalaxywavespace):
        raise RuntimeError('s2-folded-binspectra does not have same wavelength spacing as s2-folded-fullgalaxy')

    # load bininfo.txt and moments.txt
    bininfo = np.genfromtxt(
        fbininfo,
        dtype={
            'names':['binid', 'nfibers', 'flux', 'x', 'y', 'r', 'th', 'rmin', 'rmax', 'thmin', 'thmax'],
            'formats':2 * ['i4'] + 9 * ['f8']
            })

    moments = np.genfromtxt(
        fmoments,
        dtype={
            'names':['bin', 'V', 'sigma', 'h3', 'h4', 'h5', 'h6', 'Verr', 'sigmaerr', 'h3err', 'h4err', 'h5err', 'h6err'],
            'formats':['i4'] + 12 * ['f8']
            })

    if bininfo.shape[0] != moments.shape[0]:
        raise RuntimeError('bininfo and moments have different number of bins')

    newdata = np.zeros(
        bininfo.shape[0],
        dtype={
            'names': [
                'nfibers', 'flux', 'r', 'th', 'rmin', 'rmax', 'thmin', 'thmax',
                'V', 'Verr', 'sigma', 'sigmaerr', 'h3', 'h3err', 'h4', 'h4err', 'h5', 'h5err', 'h6', 'h6err'
                ],
            'formats':  20 * ['f8']
            })

    newdata['nfibers'] = bininfo['nfibers']
    newdata['flux'] = bininfo['flux']
    newdata['r'] = bininfo['r']
    newdata['th'] = bininfo['th']
    newdata['rmin'] = bininfo['rmin']
    newdata['rmax'] = bininfo['rmax']
    newdata['thmin'] = bininfo['thmin']
    newdata['thmax'] = bininfo['thmax']
    newdata['V'] = moments['V']
    newdata['Verr'] = moments['Verr']
    newdata['sigma'] = moments['sigma']
    newdata['sigmaerr'] = moments['sigmaerr']
    newdata['h3'] = moments['h3']
    newdata['h3err'] = moments['h3err']
    newdata['h4'] = moments['h4']
    newdata['h4err'] = moments['h4err']
    newdata['h5'] = moments['h5']
    newdata['h5err'] = moments['h5err']
    newdata['h6'] = moments['h6']
    newdata['h6err'] = moments['h6err']

    bincount = len(newdata)
    hdu3data = newdata if junkbins == 0 else np.delete(newdata, range(bincount - junkbins, bincount), 0)

    # create hdus
    hdu1 = fits.PrimaryHDU(hdu1data, hdu1header, 'BINDATA')
    hdu2 = fits.ImageHDU(hdu2data, hdu2header, 'GALDATA')
    hdu3 = fits.TableHDU(hdu3data, name='BINMETA')

    # make file
    hdulist = fits.HDUList([hdu1, hdu2, hdu3])
    hdulist.writeto(output)

    binspectra.close()
    fullgalaxy.close()