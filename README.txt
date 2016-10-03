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
The full list of parameters is below, broken up into sections. The basic parameters are the same as given in Table 1 of Paper V; see that table for notes and caveats. The full galaxy spectrum parameters represent two different choices for generating a composite spectrum; full spectrum 1 contains all binned fibers, while full spectrum 2 contains fibers within some smaller radius, chosen to minimize asymmetry due to masked neighbors or other data issues.

--Basic parameters:
date	(YY:MM:DD?)	date these files were generated
ra	(degrees)	Right Ascension
dec	(degrees)	Declination
d	(Mpc)		Distance
mk	(mag)		K-band magnitude
re	(arcsec)	Effective Radius
eps			Ellipticity
pa	(deg E of N)	Photometric Axis		# currently gal pa
pakin	(deg E of N)	axis used for folding		# usually matches pa, BUT
rmax	(Re)		maximum extent of binned data
env			BGG, Satellite, or Isolated
envN			number of neighbors in HDC

--Full galaxy spectrum parameters:
f1rad	(arcsec)	max radius of full spectrum 1	# currently temps1_radius
f1v	(km/s)		V of full spectrum 1		# currently gal1_V
f1sig	(km/s)		sigma of full spectrum 1	# (etc)
f1h3			h3 of full spectrum 1
f1h4			h4 of full spectrum 1
f1h5			h5 of full spectrum 1
f1h6			h6 of full spectrum 1
f2rad	(arcsec)	max radius of full spectrum 2	# currently temps2_radius
f2v	(km/s)		V of full spectrum 2		# etc
f2sig	(km/s)		sigma of full spectrum 2
f2h3			h3 of full spectrum 2
f2h4			h4 of full spectrum 2
f2h5			h5 of full spectrum 2
f2h6			h6 of full spectrum 2

--Averages over galaxy (within effective radius; flux-weighted)
sigc	(km/s)		not an average; sigma of central fiber
sigavg	(km/s)						# currently re_avgsigma
sigavge	(km/s)						# (etc)
h3avg
h3avge
h4avg
h4avge
h5avg
h5avge
h6avg
h6avge
lam			lambda within Re
rot			Fast, Unclassified, or Slow

--Best-fit parameters
sigBRs0			sigma0 for broken fit			# currently sigBR_sig0
sigBRg1			gamma1 for broken fit			# (etc)
sigBRg2			gamma2 for broken fit
sigBRx2			chisq per dof for broken fit
sigPLs0			sigma0 for single powerlaw fit
sigPLg1			gamma1 for single powerlaw fit
sigPLg2			gamma2 for single powerlaw fit
sigPLx2			chisq per dof for single powerlaw fit
h3vgrad			slope of h3 vs v/sigma
h3vgrade		slope of h3 vs v/sigma
h3vint			intercept of h3 vs v/sigma
h3vinte			intercept of h3 vs v/sigma
h4rgrad			gradient of h4 profile (see ??)
h4rint			intercept of h4 profile (see ??)	# currently h4intercept

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

