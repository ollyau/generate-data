from astropy.io import fits
import numpy as np
from utils import header, metadata

def writefits(fbinspectra, ffullgalaxy, fs3amain, fs3bmain, fmoments, rprofiles, fmeta, output):
    junkbins = int(header(rprofiles).metadata['junk bins'])

    # primary hdu (1): stack s2-folded-binspectra hdu 0 (spectra), 1 (noise), 3 (bad pixel flag), 4 (ir)
    # get wavelength data from s2-folded-binspectra hdu 2 (waves)
    binspectra = fits.open(fbinspectra)
    s3bmain = fits.open(fs3bmain)

    # indices: data[i][j][k] where i, j, k are bin, column, and data
    # columns: 0 (spectra), 1 (noise), 2 (ir), 3 (bad pixel flag), 4 (data from s3-B-folded-main.fits)
    padleft = np.where(binspectra['WAVES'].data == s3bmain['WAVES'].data[0])[0][0]
    padright = binspectra['WAVES'].data.shape[0] - np.where(binspectra['WAVES'].data == s3bmain['WAVES'].data[-1])[0][0] - 1
    s3bthing = np.pad(s3bmain[2].data, ((0,0),(padleft,padright)), mode='constant', constant_values=np.nan)
    result = np.stack((binspectra[0].data, binspectra[1].data, binspectra[4].data, binspectra[3].data, s3bthing), axis=1)

    bincount = len(result)
    hdu1data = result if junkbins == 0 else np.delete(result, range(bincount - junkbins, bincount), 0)

    binspectrawavespace = np.diff(np.log10(binspectra['WAVES'].data))
    if not np.allclose(binspectrawavespace, binspectrawavespace[0]):
        raise RuntimeError('wavelength spacing in s2-folded-binspectra is not consistent')

    s3bmainwavespace = np.diff(np.log10(s3bmain['WAVES'].data))
    if not np.allclose(s3bmainwavespace, s3bmainwavespace[0]):
        raise RuntimeError('wavelength spacing in s3-B-folded-main is not consistent')

    if not np.isclose(binspectrawavespace[0], s3bmainwavespace[0]):
        raise RuntimeError('s2-folded-binspectra does not have same wavelength spacing as s3-B-folded-main')

    meta = metadata(fmeta)
    cards = [fits.Card(keyword=k, value=v) for k, v in meta.data.iteritems()]

    hdu1header = fits.Header([
        fits.Card(keyword='PRIMARY', value='bin data'),
        fits.Card(keyword='WAVSTART', value=str(binspectra[2].data[0])),
        fits.Card(keyword='WAVEND', value=str(binspectra[2].data[-1])),
        fits.Card(keyword='WAVSPACE', value=str(binspectrawavespace[0])),
        ] + cards)

    # hdu 2: stack s2-folded-fullgalaxy.fits hdu 0 (spectra), 1 (noise), 3 (bad pixel flag), 4 (ir)
    # get wavelength data from s2-folded-fullgalaxy hdu 2 (waves) (should match binspectra)
    fullgalaxy = fits.open(ffullgalaxy)
    s3amain = fits.open(fs3amain)

    # indices: data[i][j][k] where i, j, k are bin, column, and data
    # columns: 0 (spectra), 1 (noise), 2 (ir), 3 (bad pixel flag), 4 (data from s3-A-folded-main.fits)
    padleft = np.where(fullgalaxy['WAVES'].data == s3amain['WAVES'].data[0])[0][0]
    padright = fullgalaxy['WAVES'].data.shape[0] - np.where(fullgalaxy['WAVES'].data == s3amain['WAVES'].data[-1])[0][0] - 1
    s3athing = np.pad(s3amain[2].data, ((0,0),(padleft,padright)), mode='constant', constant_values=np.nan)
    hdu2data = np.stack((fullgalaxy[0].data, fullgalaxy[1].data, fullgalaxy[4].data, fullgalaxy[3].data, s3athing), axis=1)

    fullgalaxywavespace = np.diff(np.log10(fullgalaxy['WAVES'].data))
    if not np.allclose(fullgalaxywavespace, fullgalaxywavespace[0]):
        raise RuntimeError('wavelength spacing in s2-folded-fullgalaxy is not consistent')

    s3amainwavespace = np.diff(np.log10(s3amain['WAVES'].data))
    if not np.allclose(s3amainwavespace, s3amainwavespace[0]):
        raise RuntimeError('wavelength spacing in s3-A-folded-main is not consistent')

    if not np.isclose(fullgalaxywavespace[0], s3amainwavespace[0]):
        raise RuntimeError('s2-folded-fullgalaxy does not have same wavelength spacing as s3-A-folded-main')

    hdu2header = fits.Header([
        fits.Card(keyword='WAVSTART', value=str(fullgalaxy[2].data[0])),
        fits.Card(keyword='WAVEND', value=str(fullgalaxy[2].data[-1])),
        fits.Card(keyword='WAVSPACE', value=str(fullgalaxywavespace[0])),
        ])

    # verify wavelength spacing
    if not np.allclose(binspectrawavespace, fullgalaxywavespace):
        raise RuntimeError('s2-folded-binspectra does not have same wavelength spacing as s2-folded-fullgalaxy')

    # load moments.txt (from public data generation); junk bins already discarded
    hdu3data = np.genfromtxt(fmoments, names=True)

    # create hdus
    hdu1 = fits.PrimaryHDU(hdu1data, hdu1header, 'BINSPEC')
    hdu2 = fits.ImageHDU(hdu2data, hdu2header, 'GALSPEC')
    hdu3 = fits.TableHDU(hdu3data, name='MOMENTS')

    # make file
    hdulist = fits.HDUList([hdu1, hdu2, hdu3])
    hdulist.writeto(output, clobber=True)

    binspectra.close()
    s3bmain.close()
    s3amain.close()
    fullgalaxy.close()