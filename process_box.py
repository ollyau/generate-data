import argparse
from io import BytesIO
import os
import re

from boxsdk import Client, OAuth2

from modules.fitsfile import writefits
from modules.metafile import writemeta
from modules.textfile import writetext

def main():
    desc = 'Creates public data from MASSIVE survey reduced data.'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-cid', '--clientid', required=True,
                        help='Client ID from Box API.')
    parser.add_argument('-secret', '--clientsecret', required=True,
                        help='Client secret from Box API.')
    parser.add_argument('-token', '--accesstoken', required=True,
                        help='Developer access token for Box API.')

    parser.add_argument('-i', '--include',
                        help='Comma separated list of galaxies to include.')
    parser.add_argument('-e', '--exclude',
                        help='Comma separated list of galaxies to exclude.')

    parser.add_argument('-skip', '--skipcompleted', action='store_true',
                        help='Skips galaxies that were previously processed.')

    args = vars(parser.parse_args())

    processbox(args)

def _getboxitems(f, relpath):
    dirs = [d for d in re.split(r'[\\/]+', relpath) if d is not '']
    items = f.get_items(400)
    print('getting items in {0}/{1}'.format('' if f._object_id == '0' else f.name, '/'.join(dirs)))
    for d in dirs:
        folder = next(x for x in items if x.name == d)
        items = folder.get_items(400)
    return items

def _missingfiles(galdir):
    gal = galdir.name
    galdir_contents = galdir.get_items(10)

    dataname = gal + '-folded-moments.txt'
    try:
        data = next(x for x in galdir_contents if x.name == dataname)
    except StopIteration:
        return True

    fitsname = gal + '-folded-spectra.fits'
    try:
        fits = next(x for x in galdir_contents if x.name == fitsname)
    except StopIteration:
        return True

    metaname = gal + '-folded-misc.txt'
    try:
        meta = next(x for x in galdir_contents if x.name == metaname)
    except StopIteration:
        return True

    return not all(['data' in locals(), 'fits' in locals(), 'meta' in locals()])

# get a client id, client secret, and 1 hour developer access token at https://berkeley.app.box.com/developers/services
def processbox(args):
    cid = args['clientid']
    secret = args['clientsecret']
    token = args['accesstoken']

    oauth = OAuth2(client_id=cid, client_secret=secret, access_token=token)
    client = Client(oauth)
    root = client.folder('0')

    galdirs_in = _getboxitems(root, r'MASSIVE/Reduced-Data')
    search = re.compile(r'^[A-Z]+\d+$').search

    # create root output folder
    rootdirs = root.get_items(100)
    try:
        output_root = next(x for x in rootdirs if x.name == 'Output')
    except StopIteration:
        output_root = root.create_subfolder('Output')

    galaxies = set(m.group(0) for m in (search(g.name) for g in galdirs_in) if m)

    if args['skipcompleted']:
        prev_galdirs_out = output_root.get_items(400)
        completed = set(prev_galdir.name for prev_galdir in prev_galdirs_out if not _missingfiles(prev_galdir))
        galaxies = galaxies.difference(completed)

    if args['include'] is not None:
        include = [x.strip() for x in args['include'].split(',') if x and not x.isspace()]
        galaxies = galaxies.intersection(include)

    if args['exclude'] is not None:
        exclude = [x.strip() for x in args['exclude'].split(',') if x and not x.isspace()]
        galaxies = galaxies.difference(exclude)

    for galdir_in in galdirs_in:
        m = search(galdir_in.name)
        if not m:
            print('skipped Reduced-Data/{0}'.format(galdir_in.name))
            continue
        gal = m.group(0)

        if gal not in galaxies:
            continue

        print('processing {0}'.format(gal))

        try:
            files = _getboxitems(galdir_in, r'kinematics_paperversion/more_files')
        except StopIteration:
            print('warning: missing data subdirectory ({0}/kinematics_paperversion/more_files)'.format(gal))
            continue

        file_s2_folded_binspectra = next(x for x in files if x.name == gal + '-s2-folded-binspectra.fits')
        file_s2_folded_fullgalaxy = next(x for x in files if x.name == gal + '-s2-folded-fullgalaxy.fits')
        file_s2_folded_bininfo = next(x for x in files if x.name == gal + '-s2-folded-bininfo.txt')
        file_s3_A_folded_temps_1 = next(x for x in files if x.name == gal + '-s3-A-folded-temps-1.txt')
        file_s3_A_folded_temps_2 = next(x for x in files if x.name == gal + '-s3-A-folded-temps-2.txt')
        file_s3_B_folded_moments = next(x for x in files if x.name == gal + '-s3-B-folded-moments.txt')
        file_s4_folded_rprofiles = next(x for x in files if x.name == gal + '-s4-folded-rprofiles.txt')
        file_s2_params = next(x for x in files if x.name == gal + '_s2_params.txt')

        with BytesIO() as s2_folded_binspectra, \
             BytesIO() as s2_folded_fullgalaxy, \
             BytesIO() as s2_folded_bininfo, \
             BytesIO() as s3_A_folded_temps_1, \
             BytesIO() as s3_A_folded_temps_2, \
             BytesIO() as s3_B_folded_moments, \
             BytesIO() as s4_folded_rprofiles, \
             BytesIO() as s2_params, \
             BytesIO() as fits_output, \
             BytesIO() as data_output, \
             BytesIO() as meta_output:

            print('downloading {0}'.format(file_s2_folded_binspectra.name))
            file_s2_folded_binspectra.download_to(s2_folded_binspectra)

            print('downloading {0}'.format(file_s2_folded_fullgalaxy.name))
            file_s2_folded_fullgalaxy.download_to(s2_folded_fullgalaxy)

            print('downloading {0}'.format(file_s2_folded_bininfo.name))
            file_s2_folded_bininfo.download_to(s2_folded_bininfo)

            print('downloading {0}'.format(file_s3_A_folded_temps_1.name))
            file_s3_A_folded_temps_1.download_to(s3_A_folded_temps_1)

            print('downloading {0}'.format(file_s3_A_folded_temps_2.name))
            file_s3_A_folded_temps_2.download_to(s3_A_folded_temps_2)

            print('downloading {0}'.format(file_s3_B_folded_moments.name))
            file_s3_B_folded_moments.download_to(s3_B_folded_moments)

            print('downloading {0}'.format(file_s4_folded_rprofiles.name))
            file_s4_folded_rprofiles.download_to(s4_folded_rprofiles)

            print('downloading {0}'.format(file_s2_params.name))
            file_s2_params.download_to(s2_params)

            print('creating text file for {0}'.format(gal))
            s2_folded_bininfo.seek(0)
            s3_B_folded_moments.seek(0)
            s4_folded_rprofiles.seek(0)
            writetext(s2_folded_bininfo, s3_B_folded_moments, s4_folded_rprofiles, data_output)

            print('creating metadata file for {0}'.format(gal))
            s2_folded_bininfo.seek(0)
            s2_params.seek(0)
            s3_A_folded_temps_1.seek(0)
            s3_A_folded_temps_2.seek(0)
            s3_B_folded_moments.seek(0)
            s4_folded_rprofiles.seek(0)
            writemeta(gal, meta_output, s2_folded_bininfo, s3_A_folded_temps_1, s3_A_folded_temps_2, s2_params, s3_B_folded_moments, s4_folded_rprofiles)

            print('creating fits file for {0}'.format(gal))
            s2_folded_binspectra.seek(0)
            s2_folded_fullgalaxy.seek(0)
            s2_folded_bininfo.seek(0)
            s4_folded_rprofiles.seek(0)
            data_output.seek(0)
            meta_output.seek(0)
            writefits(s2_folded_binspectra, s2_folded_fullgalaxy, s2_folded_bininfo, data_output, s4_folded_rprofiles, meta_output, fits_output)

            data_output.seek(0)
            meta_output.seek(0)
            fits_output.seek(0)

            print('uploading new data for {0}'.format(gal))

            # create per-galaxy output folder
            galdirs_out = output_root.get_items(400)
            try:
                gal_output = next(x for x in galdirs_out if x.name == gal)
            except StopIteration:
                gal_output = output_root.create_subfolder(gal)

            prev_output = gal_output.get_items(10)

            dataname = gal + '-folded-moments.txt'
            try:
                dest = next(x for x in prev_output if x.name == dataname)
                dest.update_contents_with_stream(data_output)
            except StopIteration:
                gal_output.upload_stream(data_output, dataname)

            fitsname = gal + '-folded-spectra.fits'
            try:
                dest = next(x for x in prev_output if x.name == fitsname)
                dest.update_contents_with_stream(fits_output)
            except StopIteration:
                gal_output.upload_stream(fits_output, fitsname)

            metaname = gal + '-folded-misc.txt'
            try:
                dest = next(x for x in prev_output if x.name == metaname)
                dest.update_contents_with_stream(meta_output)
            except StopIteration:
                gal_output.upload_stream(meta_output, metaname)

if __name__ == '__main__':
    main()
