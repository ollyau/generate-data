import argparse
import os
import re

from astropy.io import fits

import numpy as np

import matplotlib as mpl
import matplotlib.colors as colors
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Wedge, Circle

from utils import metadata

def main():
    parser = argparse.ArgumentParser(description='Creates plots from MASSIVE survey public data.')
    parser.add_argument('-d', '--directory', help='Directory path containing fits, txt, and metadata txt files.', required=True)
    parser.add_argument('-o', '--output', help='Path to destination directory.', required=True)
    parser.add_argument('-i', '--include', help='Comma separated list of galaxies to include.')
    parser.add_argument('-e', '--exclude', help='Comma separated list of galaxies to exclude.')
    parser.add_argument('-s', '--skip-completed', help='Skips galaxies that were previously processed.')

    args = vars(parser.parse_args())

    files = os.listdir(args['directory'])
    search = re.compile(r'^((?:NGC|UGC)\d+)(?:(?:_meta\.txt)|\.(?:txt|fits))$').search
    galaxies = sorted(set(m.group(1) for m in (search(f) for f in files) if m))

    if args['skip-completed'] is not None:
        search1 = re.compile(r'^((?:NGC|UGC)\d+)\.pdf$').search
        completedfiles = os.listdir(args['output'])
        completed = set(m.group(1) for m in (search1(f) for f in completedfiles) if m)
        galaxies = galaxies.difference(completed)

    if args['include'] is not None:
        include = [x.strip() for x in args['include'].split(',') if x and not x.isspace()]
        galaxies = galaxies.intersection(include)

    if args['exclude'] is not None:
        exclude = [x.strip() for x in args['exclude'].split(',') if x and not x.isspace()]
        galaxies = galaxies.difference(exclude)

    for g in galaxies:
        dest = os.path.join(args['output'], '{0}.pdf'.format(g))
        fitsfile = os.path.join(args['directory'], '{0}.fits'.format(g))
        data = os.path.join(args['directory'], '{0}.txt'.format(g))
        meta = os.path.join(args['directory'], '{0}_meta.txt'.format(g))
        print('plotting {0}'.format(dest))
        plot(g, dest, fitsfile, data, meta)

def plot(name, destination, fitsfile, data, meta):
    pdf = PdfPages(destination)
    plotbinflux(pdf, name, fitsfile, meta)
    plotbins2n(pdf, name, fitsfile, meta)
    plotmomentradius(pdf, name, data, meta)
    plotspectra(pdf, name, fitsfile)
    pdf.close()

def _multiaxes(fig, rows, cols, count, **kwargs):
    border = kwargs['border'] if 'border' in kwargs else (0.1, 0.1, 0.1, 0.1) # left, top, right, bottom
    hspacing, vspacing = kwargs['spacing'] if 'spacing' in kwargs else (0.1, 0.1)
    width = (1.0 - border[0] - border[2] - (hspacing * (cols - 1))) / cols
    height = (1.0 - border[1] - border[3] - (vspacing * (rows - 1))) / rows
    return [
        fig.add_axes([border[0] + (col * (width + hspacing)), border[3] + (row * (height + vspacing)), width, height])
        for row in xrange(rows - 1, -1, -1) if len(fig.axes) < count
        for col in xrange(cols) if len(fig.axes) < count
        ]

def _get_log_mappable(xmin, xmax, cmap):
    mappable = plt.cm.ScalarMappable(norm=colors.LogNorm(vmin=xmin, vmax=xmax), cmap=cmap)
    mappable.set_array([xmin, xmax])
    mappable.set_clim(vmin=xmin, vmax=xmax)
    return mappable

def plotbinflux(pdf, name, fitsfile, metafile):
    patches = []
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_axes([0.117647, 0.204545, 0.764706, 0.590909])

    hdulist = fits.open(fitsfile)

    mappable = _get_log_mappable(min(hdulist[2].data['flux']), max(hdulist[2].data['flux']), 'Reds')
    for binmeta in hdulist[2].data:
        if np.isnan(binmeta['rmin']):
            center = (binmeta['r'] * np.cos(np.deg2rad(binmeta['th'] + 90.0)), binmeta['r'] * np.sin(np.deg2rad(binmeta['th'] + 90.0)))
            patches.append(Circle(center, 2.1, facecolor=mappable.to_rgba(binmeta['flux']), lw=0.2))
            continue
        else:
            patches.append(Wedge(
                (0.0, 0.0),
                binmeta['rmax'],
                90.0 + binmeta['thmin'],
                90.0 + binmeta['thmax'],
                width=binmeta['rmax'] - binmeta['rmin'],
                facecolor=mappable.to_rgba(binmeta['flux']),
                lw=1.5
                ))

    meta = metadata(metafile)
    gal_pa = float(meta.data['gal pa'])
    fullbin_radius = float(meta.data['temps2_radius'])

    patches.append(Circle((0.0, 0.0), fullbin_radius, facecolor='none', ls='dashed'))

    maxr = max(hdulist[2].data['r']) * 1.135
    xvals = np.linspace(-maxr, maxr, maxr * 20)
    ax.plot(xvals, np.tan(np.deg2rad(gal_pa - 90.0)) * xvals, color='red', lw=1.5)
    ax.axis('equal')
    ax.set_xlim(-maxr, maxr)
    ax.set_ylim(-maxr, maxr)

    ax.add_collection(PatchCollection(patches, match_original=True))

    cax = fig.add_axes([0.117647, 0.885, 0.764706, 0.035])
    fig.colorbar(cax=cax, mappable=mappable, orientation='horizontal', label='flux [erg / (cm2 s)]')

    ax.set_xlabel(r'$\leftarrow$east (arcsec) west$\rightarrow$', labelpad=5)
    ax.set_ylabel(r'$\leftarrow$south (arcsec) north$\rightarrow$', labelpad=5)
    fig.suptitle(name + ' Bin flux map')
    pdf.savefig(fig)
    plt.close(fig)

    hdulist.close()

def plotbins2n(pdf, name, fitsfile, metafile):
    patches = []
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_axes([0.117647, 0.204545, 0.764706, 0.590909])

    hdulist = fits.open(fitsfile)

    actual = [np.nanmean(x[0]) for x in hdulist[0].data]
    noise = [np.nanmean(x[1]) for x in hdulist[0].data]

    s2n = np.divide(actual, noise)

    xmin = np.amin(s2n)
    xmax = np.amax(s2n)

    mappable = _get_log_mappable(xmin, xmax, 'Greens')

    for binmeta, bins2n in zip(hdulist[2].data, s2n):
        if np.isnan(binmeta['rmin']):
            center = (binmeta['r'] * np.cos(np.deg2rad(binmeta['th'] + 90.0)), binmeta['r'] * np.sin(np.deg2rad(binmeta['th'] + 90.0)))
            patches.append(Circle(center, 2.1, facecolor=mappable.to_rgba(bins2n), lw=0.2))
            continue
        else:
            patches.append(Wedge(
                (0.0, 0.0),
                binmeta['rmax'],
                90.0 + binmeta['thmin'],
                90.0 + binmeta['thmax'],
                width=binmeta['rmax'] - binmeta['rmin'],
                facecolor=mappable.to_rgba(bins2n),
                lw=1.5
                ))

    meta = metadata(metafile)
    gal_pa = float(meta.data['gal pa'])
    fullbin_radius = float(meta.data['temps2_radius'])

    patches.append(Circle((0.0, 0.0), fullbin_radius, facecolor='none', ls='dashed'))

    maxr = max(hdulist[2].data['r']) * 1.135
    xvals = np.linspace(-maxr, maxr, maxr * 20)
    ax.plot(xvals, np.tan(np.deg2rad(gal_pa - 90.0)) * xvals, color='red', lw=1.5)
    ax.axis('equal')
    ax.set_xlim(-maxr, maxr)
    ax.set_ylim(-maxr, maxr)

    ax.add_collection(PatchCollection(patches, match_original=True))

    cax = fig.add_axes([0.117647, 0.885, 0.764706, 0.035])
    fig.colorbar(cax=cax, mappable=mappable, orientation='horizontal', label='s2n')

    ax.set_xlabel(r'$\leftarrow$east (arcsec) west$\rightarrow$', labelpad=5)
    ax.set_ylabel(r'$\leftarrow$south (arcsec) north$\rightarrow$', labelpad=5)
    fig.suptitle(name + ' Bin s2n map')
    pdf.savefig(fig)
    plt.close(fig)

    hdulist.close()

def anglenorm(angle, gal_pa):
    if angle <= gal_pa and angle >= gal_pa - 180.0:
        result = -angle + gal_pa
    elif angle >= gal_pa and angle <= gal_pa + 180.0:
        result = angle - gal_pa
    elif angle < gal_pa - 180.0 and angle > gal_pa - 360.0:
        result = anglenorm(angle + 360.0, gal_pa)
    elif angle > gal_pa + 180.0 and angle < gal_pa + 360.0:
        result = anglenorm(angle - 360.0, gal_pa)
    else:
        assert False, 'unable to normalize angle (input: {0}, gal pa: {1})'.format(angle, gal_pa)
    if result < 0 or result > 180:
        assert False, 'normalized angle {0} not in [0,180] range (input: {1}, gal pa: {2})'.format(result, angle, gal_pa)
    return result

def plotmomentradius(pdf, name, datafile, metafile):
    fig = plt.figure(figsize=(8.5, 11))
    axes = _multiaxes(fig, 3, 2, 6, border=(0.1235295, 0.063636, 0.082353, 0.127273), spacing=(0.1, 0.07))

    cxmin = 0
    cxmax = 180.0
    mappable = plt.cm.ScalarMappable(cmap='bone')
    mappable.set_array([cxmin, cxmax])
    mappable.set_clim(vmin=cxmin, vmax=cxmax)
    cax = fig.add_axes([0.082353, 0.063636, 0.835294, 0.015909])
    fig.colorbar(cax=cax, mappable=mappable, orientation='horizontal', ticks=xrange(0, 181, 20), label='Angle (degrees)')

    meta = metadata(metafile)
    v = float(meta.data['gal1_V'])
    gal_pa = float(meta.data['gal pa'])

    data = np.genfromtxt(datafile, names=True)

    originalfontsize = mpl.rcParams['font.size']
    originallegendsize = mpl.rcParams['legend.fontsize']

    mpl.rc('font', size=10)
    mpl.rc('legend', fontsize=10)

    for mname, mcol, ax in zip(['V', 'sigma', 'h3', 'h4', 'h5', 'h6'], ['V', 'sig', 'h3', 'h4', 'h5', 'h6'], axes):
        moments = np.subtract(data[mcol], v) if mcol == 'V' else data[mcol]
        error = data[mcol + 'err']
        radius = data['r']
        theta = [anglenorm(th, gal_pa) for th in data['th']]

        ax.errorbar(radius, moments, yerr=error, fmt='none', ecolor='k', zorder=-1, capsize=0)
        ax.scatter(radius, moments, c=mappable.to_rgba(theta), s=50.0, alpha=0.8, linewidths=0.5)

        ax.set_xlim(left=0)
        ax.set_xlabel('radius', labelpad=5)
        ax.set_ylabel(mname, labelpad=5)

    fig.suptitle('{0} Moment vs radius'.format(name))
    pdf.savefig(fig)
    plt.close(fig)

    mpl.rcParams['font.size'] = originalfontsize
    mpl.rcParams['legend.fontsize'] = originallegendsize

def plotspectra(pdf, name, fitsfile):
    hdulist = fits.open(fitsfile)

    wavstart = float(hdulist[0].header['WAVSTART'])
    wavend = float(hdulist[0].header['WAVEND'])
    wavspace = float(hdulist[0].header['WAVSPACE'])

    wavcount = int(round((np.log10(wavend) - np.log10(wavstart)) / wavspace)) + 1
    xvals = np.logspace(np.log10(wavstart), np.log10(wavend), wavcount)
    if wavcount != hdulist[0].data.shape[2]:
        raise RuntimeError('calculated wavelength range does not match spectra data')

    binsperpage = 8
    segments = [hdulist[0].data[i:i + binsperpage] for i in xrange(0, len(hdulist[0].data), binsperpage)]

    for i, s in enumerate(segments):
        fig = plt.figure(figsize=(8.5, 11))
        ax = fig.add_axes([0.082353, 0.063636, 0.835294, 0.872727])

        for j, bindata in enumerate(s):
            binspectra_median = np.nanmedian(bindata[0])
            offset = (i * binsperpage) + j + 1 + abs(np.nanmean(bindata[0][:10]) / binspectra_median)
            ax.plot(xvals, (-bindata[0] / binspectra_median) + offset, color='black')

        ymin = (i * binsperpage) + 1
        ymax = min((i + 1) * binsperpage, len(hdulist[0].data))
        ax.set_yticks(xrange(ymin, ymax + 1))
        ax.set_xlim(xvals[0], xvals[-1])
        ax.set_ylim(ymin - 2, ((i + 1) * binsperpage) + 1)
        ax.invert_yaxis()
        ax.set_xlabel('wavelength (angstroms)', labelpad=5)
        fig.suptitle('{0} bin spectra by bin number ({1})'.format(name, '{0}-{1}'.format(ymin, ymax) if ymin != ymax else ymax))
        pdf.savefig(fig)
        plt.close(fig)

    hdulist.close()

if __name__ == '__main__':
    main()