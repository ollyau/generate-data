from astropy.io import fits
import numpy as np
from utils import header, metadata

def writefits(fbinspectra, ffullgalaxy, fbininfo, fmoments, rprofiles, fmeta, output):
    junkbins = int(header(rprofiles).metadata['junk bins'])

    # primary hdu (1): stack s2-folded-binspectra hdu 0 (spectra), 1 (noise), 3 (bad pixel flag), 4 (ir)
    # get wavelength data from s2-folded-binspectra hdu 2 (waves)
    binspectra = fits.open(fbinspectra)

    # indices: data[i][j][k] where i, j, k are bin, column, and data
    # columns: 0 (spectra), 1 (noise), 2 (ir), 3 (bad pixel flag)
    result = np.stack((binspectra[0].data, binspectra[1].data, binspectra[4].data, binspectra[3].data), axis=1)

    bincount = len(result)
    hdu1data = result if junkbins == 0 else np.delete(result, range(bincount - junkbins, bincount), 0)

    binspectrawavespace = np.diff(np.log10(binspectra[2].data))
    if not np.allclose(binspectrawavespace, binspectrawavespace[0]):
        raise RuntimeError('wavelength spacing in s2-folded-binspectra is not consistent')

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

    # load moments.txt (from public data generation); junk bins already discarded
    hdu3data = np.genfromtxt(fmoments, names=True)

    # load bininfo.txt
    bininfo = np.genfromtxt(fbininfo, names=True, skip_header=1, usecols=(7, 8, 9, 10))
    bincount = len(bininfo)
    hdu4data = bininfo if junkbins == 0 else np.delete(bininfo, range(bincount - junkbins, bincount), 0)

    # create hdus
    hdu1 = fits.PrimaryHDU(hdu1data, hdu1header, 'BINSPEC')
    hdu2 = fits.ImageHDU(hdu2data, hdu2header, 'GALSPEC')
    hdu3 = fits.TableHDU(hdu3data, name='MOMENTS')
    hdu4 = fits.TableHDU(hdu4data, name='BINEXTRA')

    # make file
    hdulist = fits.HDUList([hdu1, hdu2, hdu3, hdu4])
    hdulist.writeto(output)

    binspectra.close()
    fullgalaxy.close()
