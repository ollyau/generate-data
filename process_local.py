import argparse
import os
import re

from modules.textfile import writetext
from modules.fitsfile import writefits
from modules.metafile import writemeta


def _outputpathlist(outputdir, gal):
    file_endings = ['-folded-moments.txt',
                    '-folded-spectra.fits',
                    '-folded-misc.txt']
    return [os.path.join(outputdir, gal, gal + e) for e in file_endings]
    
def _missingfiles(outputdir, gal):
    return all([os.path.isfile(f) for f in _outputpathlist(outputdir, gal)])

def _processgal(inputdir, outputdir, gal):
    galdir_in = os.path.join(inputdir, gal, 'kinematics_paperversion',
                             'more_files')
    if not os.path.isdir(galdir_in):
        print 'No paperversion for {}, skipping to next galaxy'.format(gal)
        return
    s2_binspectra = os.path.join(galdir_in, gal + '-s2-folded-binspectra.fits')
    s2_fullgalaxy = os.path.join(galdir_in, gal + '-s2-folded-fullgalaxy.fits')
    s2_bininfo = os.path.join(galdir_in, gal + '-s2-folded-bininfo.txt')
    s3_A_temps_1 = os.path.join(galdir_in, gal + '-s3-A-folded-temps-1.txt')
    s3_A_temps_2 = os.path.join(galdir_in, gal + '-s3-A-folded-temps-2.txt')
    s3_B_moments = os.path.join(galdir_in, gal + '-s3-B-folded-moments.txt')
    s4_rprofiles = os.path.join(galdir_in, gal + '-s4-folded-rprofiles.txt')
    s2_params = os.path.join(galdir_in, gal + '_s2_params.txt')
    
    galdir_out = os.path.join(outputdir, gal)
    if not os.path.exists(galdir_out):
        os.makedirs(galdir_out)

    outputpaths = _outputpathlist(outputdir, gal)
    with open(outputpaths[0], 'wb') as data_output, \
         open(outputpaths[1], 'wb') as fits_output, \
         open(outputpaths[2], 'wb') as meta_output:
        writetext(s2_bininfo, s3_B_moments, s4_rprofiles, data_output)
        writefits(s2_binspectra, s2_fullgalaxy, s2_bininfo, s3_B_moments,
                  s4_rprofiles, fits_output)
        writemeta(meta_output, s2_bininfo, s3_A_temps_1, s3_A_temps_2,
                  s2_params, s3_B_moments, s4_rprofiles)
    

def main():
    desc = 'Creates public data from MASSIVE survey reduced data.'
    parser = argparse.ArgumentParser(description=desc)

    # required arguments
    parser.add_argument('-d', '--directory',
                        help='Path to Reduced-Data folder.')
    parser.add_argument('-o', '--output',
                        help='Path to destination directory.')

    # optional arguments
    parser.add_argument('-i', '--include',
                        help='Comma separated list of galaxies to include.')
    parser.add_argument('-e', '--exclude',
                        help='Comma separated list of galaxies to exclude.')

    parser.add_argument('-skip', '--skipcompleted',
                        help='Skips galaxies that were previously processed.')

    args = vars(parser.parse_args())
    if args['directory'] is None or args['output'] is None:
        raise ValueError('invalid argument input')
    datadir = args['directory']
    outputdir = args['output']

    files = os.listdir(datadir)
    search = re.compile(r'^[A-Z]+\d+$').search
    galaxies = sorted(set(m.group(0) for m in (search(f) for f in files) if m))

    if args['skipcompleted'] is not None:
        alldirs = os.listdir(outputdir)
        galdirs = set(m.group(0) for m in (search(f) for f in alldirs) if m)
        completed = [x for x in galdirs if not _missingfiles(outputdir, x)]
        galaxies = galaxies.difference(completed)

    if args['include'] is not None:
        include = [x.strip() for x in args['include'].split(',')
                   if x and not x.isspace()]
        galaxies = galaxies.intersection(include)

    if args['exclude'] is not None:
        exclude = [x.strip() for x in args['exclude'].split(',')
                   if x and not x.isspace()]
        galaxies = galaxies.difference(exclude)

    for g in galaxies:
        print 'Processing {}'.format(g)
        _processgal(datadir, outputdir, g)

if __name__ == '__main__':
    main()
