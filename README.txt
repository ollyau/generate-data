This readme explains the contents of each of the three files available for the MASSIVE galaxies with folded, binned spectra and kinematic analysis. These files are based on the analysis and data in Paper V of the MASSIVE survey.

=============================
A brief summary of the files:
=============================

1) NGC0000-folded-misc.txt:
Summary text file with all single-number-per-galaxy quantities. This includes averages over the whole galaxy of each moment (V, sigma, etc), best-fit parameters for various profile fits, and basic parameters like distance, K-band magnitude, ellipticity, etc.

2) NGC0000-folded-moments.txt:
Mainly contains ppxf moments (V, sigma, h3, h4, h5, h6) and errors for each bin. Other useful information like bin coordinates and fluxes are included.

3) NGC0000-folded-spectra.fits:
Binned spectra (including noise, instrument resolution, and bad pixel mask), both for folded bins and for the whole galaxy and a central fiber region of each galaxy. Data from the above text files is also included.

====================================
A detailed explanation of each file:
====================================

1) NGC0000-folded-misc.txt:
--------------------
The full list of parameters is below, broken up into sections. The basic parameters are the same as given in Table 1 of Paper V; see that table for notes and caveats. The full galaxy spectrum parameters represent two different choices for generating a composite spectrum; full spectrum 1 contains all fibers, while full spectrum 2 contains fibers within some smaller radius, chosen to minimize asymmetry due to masked neighbors or other issues.

#
# Basic parameters:
#
galaxy			name of galaxy
date			ISO 8601 timestamp of when files were generated (UTC)
ra	(degrees)	Right Ascension
dec	(degrees)	Declination
d	(Mpc)		Distance
mk	(mag)		K-band magnitude
re	(arcsec)	Effective Radius
eps			Ellipticity
pa	(deg E of N)	Photometric Axis
pakin	(deg E of N)	axis used for folding (usually matches PA but not always)
rmax	(Re)		maximum extent of binned data
env			BGG, Satellite, or Isolated
envN			number of neighbors in 2MRS HDC
mhalo	(log10 Msun)	halo mass in 2MRS HDC

#
# Full galaxy spectrum parameters:
#
f1rad	(arcsec)	max radius of full spectrum 1
f1v	(km/s)		V of full spectrum 1
f1sig	(km/s)		sigma of full spectrum 1
f1h3			h3 of full spectrum 1
f1h4			h4 of full spectrum 1
f1h5			h5 of full spectrum 1
f1h6			h6 of full spectrum 1
f2rad	(arcsec)	max radius of full spectrum 2
f2v	(km/s)		V of full spectrum 2
f2sig	(km/s)		sigma of full spectrum 2
f2h3			h3 of full spectrum 2
f2h4			h4 of full spectrum 2
f2h5			h5 of full spectrum 2
f2h6			h6 of full spectrum 2

#
# Averages over galaxy (within effective radius; flux-weighted)
#
sigc	(km/s)		not an average; sigma of central fiber
sigavg	(km/s)		average sigma
sigavge	(km/s)		error on average sigma (statistical only)
h3avg			average h3
h3avge			error on average h3 (statistical only)
h4avg			average h4
h4avge			error on average h4 (statistical only)
h5avg			average h5
h5avge			error on average h5 (statistical only)
h6avg			average h6
h6avge			error on average h6 (statistical only)
lam			lambda within Re

#
# Best-fit parameters
#
sigBRs0			sigma0 for broken powerlaw fit
sigBRg1			gamma1 for broken powerlaw fit
sigBRg2			gamma2 for broken powerlaw fit
sigBRx2			chisq per dof for broken powerlaw fit
sigPLs0			sigma0 for single powerlaw fit
sigPLg2			gamma2 for single powerlaw fit (gamma1=gamma2)
sigPLx2			chisq per dof for single powerlaw fit
h3vgrad			slope of h3 vs v/sigma
h3vgrade		error on slope of h3 vs v/sigma
h3vint			intercept of h3 vs v/sigma
h3vinte			error on intercept of h3 vs v/sigma
h4rgrad			slope of h4 vs log r
h4rint			intercept of h4 vs log r

2) NGC0000-folded-moments.txt:
-----------------------
Each row represents a single folded bin; they are sorted by bin radius. In order to get the bin luminosity for purposes of luminosity weighting, multiply nf*flux; number of fibers is equivalent to area, since all fibers have equal coverage. (Note that the units are arbitrary, so this is only gives luminosity in a relative sense within the galaxy.) Radial profiles can be constructed by taking a luminosity-weighted average of some quantity over bins with the same annulus number; this corresponds obviously to the binned annuli in the outer regions, and divides the inner single-fiber bins into some reasonable number of annuli.

--The columns are as follows:
bin			bin number
nf			number of fibers in bin
ann			annulus number (used to create radial profiles)
flux			average bin flux, in arbitrary units
r	(arcsec)	bin radius
th	(deg E of N)	angle theta of bin
V
Ve
sig
sige
[hN]			higher moments h3, h4, h5, h6
[hNe]			errors on higher moments


3) NGC0000-folded-spectra.fits:
------------------------
There are a total of 4 HDUs in the FITS file.

The first and second HDUs provide spectra, noise, instrument resolution, and bad pixel data.  The first (primary) HDU has this data for each bin, as well as the metadata from folded-misc.txt as header cards.  The second HDU contains full galaxy data instead of data per bin.  Both the first and second HDUs have header cards to describe the wavelength range of the spectra.  The first two HDUs have a multi-dimensional data array arranged as follows: data[i][j][k] where i, j, k are bin, column, and data.  The value of j ("column") can be 0, 1, 2, or 3, corresponding to spectra, noise, instrument resolution, and bad pixel data respectively.

The third HDU is a table HDU with the contents of folded-moments.txt; see previous section for documentation of values.

The fourth HDU is a table HDU containing additional information (rmin rmax thmin thmax) for each bin.
