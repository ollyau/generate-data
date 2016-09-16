import argparse
import os
import re
from io import BytesIO

try:
    from boxsdk import Client, OAuth2
except Exception as e:
    print '\n=================='
    print 'Error in imports: ',e
    print '------------------'
    print ('Everything will run fine as long as you are not'
           ' trying to use the Box API')
    print '==================\n'

from fits import createfits
from metadata import writemeta
from text import joindata

def main():
    parser = argparse.ArgumentParser(description='Creates public data from MASSIVE survey reduced data.')

    parser.add_argument('-d', '--directory', help='Path to Reduced-Data folder.')
    parser.add_argument('-o', '--output', help='Path to destination directory.')

    parser.add_argument('-cid', '--client-id', help='Client ID from Box API.')
    parser.add_argument('-secret', '--client-secret', help='Client secret from Box API.')
    parser.add_argument('-token', '--access-token', help='Developer access token for Box API.')

    parser.add_argument('-i', '--include', help='Comma separated list of galaxies to include.')
    parser.add_argument('-e', '--exclude', help='Comma separated list of galaxies to exclude.')

    parser.add_argument('-skip', '--skip-completed', help='Skips galaxies that were previously processed.')

    args = vars(parser.parse_args())
    if args['directory'] is not None and args['output'] is not None:
        processlocal(args)
    elif args['client-id'] is not None and args['client-secret'] is not None and args['access-token'] is not None:
        processbox(args)
    else:
        raise ValueError('invalid argument input')

def processlocal(args):
    datadir = args['directory']
    outputdir = args['output']

    files = os.listdir(datadir)
    search = re.compile(r'^(?:NGC|UGC)\d+$').search
    galaxies = sorted(set(m.group(0) for m in (search(f) for f in files) if m))

    if args['skip-completed'] is not None:
        search1 = re.compile(r'^((?:NGC|UGC)\d+)\.(?:txt|fits)$').search
        completedfiles = os.listdir(outputdir)
        completed = set(m.group(1) for m in (search1(f) for f in completedfiles) if m)
        galaxies = galaxies.difference(completed)

    if args['include'] is not None:
        include = [x.strip() for x in args['include'].split(',') if x and not x.isspace()]
        galaxies = galaxies.intersection(include)

    if args['exclude'] is not None:
        exclude = [x.strip() for x in args['exclude'].split(',') if x and not x.isspace()]
        galaxies = galaxies.difference(exclude)

    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    for g in galaxies:
        filesdir = os.path.join(datadir, g, 'kinematics_paperversion', 'more_files')

        s2_folded_binspectra = os.path.join(filesdir, g + '-s2-folded-binspectra.fits')
        s2_folded_fullgalaxy = os.path.join(filesdir, g + '-s2-folded-fullgalaxy.fits')
        s2_folded_bininfo = os.path.join(filesdir, g + '-s2-folded-bininfo.txt')
        s3_A_folded_temps_1 = os.path.join(filesdir, g + '-s3-A-folded-temps-1.txt')
        s3_A_folded_temps_2 = os.path.join(filesdir, g + '-s3-A-folded-temps-2.txt')
        s3_B_folded_moments = os.path.join(filesdir, g + '-s3-B-folded-moments.txt')
        s4_folded_rprofiles = os.path.join(filesdir, g + '-s4-folded-rprofiles.txt')
        s2_params = os.path.join(filesdir, g + '_s2_params.txt')

        with open(os.path.join(outputdir, g + '.txt'), 'wb') as data_output, \
             open(os.path.join(outputdir, g + '.fits'), 'wb') as fits_output, \
             open(os.path.join(outputdir, g + '_meta.txt'), 'wb') as meta_output:

            joindata(s2_folded_bininfo, s3_B_folded_moments, s4_folded_rprofiles, data_output)
            createfits(s2_folded_binspectra, s2_folded_fullgalaxy, s2_folded_bininfo, s3_B_folded_moments, s4_folded_rprofiles, fits_output)
            writemeta(s2_folded_bininfo, s3_A_folded_temps_1, s3_A_folded_temps_2, s2_params, meta_output)

def _getboxitems(f, relpath):
    dirs = [d for d in re.split(r'[\\/]+', relpath) if d is not '']
    items = f.get_items(100)
    print('getting items in {0}/{1}'.format('' if f._object_id == '0' else f.name, '/'.join(dirs)))
    for d in dirs:
        folder = next(x for x in items if x.name == d)
        items = folder.get_items(100)
    return items

# get a client id, client secret, and 1 hour developer access token at https://berkeley.app.box.com/developers/services
def processbox(args):
    cid = args['client-id']
    secret = args['client-secret']
    token = args['access-token']

    oauth = OAuth2(client_id=cid, client_secret=secret, access_token=token)
    client = Client(oauth)
    root = client.folder('0')

    dataitems = _getboxitems(root, r'Test/Reduced-Data')
    search = re.compile(r'^(?:NGC|UGC)\d+$').search

    # create output folder
    rootdirs = root.get_items(100)
    try:
        outputfolder = next(x for x in rootdirs if x.name == 'Output')
    except StopIteration:
        outputfolder = root.create_subfolder('Output')

    previousoutput = outputfolder.get_items(400)

    galaxies = set(m.group(0) for m in (search(g.name) for g in dataitems) if m)

    if args['skip-completed'] is not None:
        search1 = re.compile(r'^((?:NGC|UGC)\d+)\.(?:txt|fits)$').search
        completed = set(m.group(1) for m in (search1(g.name) for g in previousoutput) if m)
        galaxies = galaxies.difference(completed)

    if args['include'] is not None:
        include = [x.strip() for x in args['include'].split(',') if x and not x.isspace()]
        galaxies = galaxies.intersection(include)

    if args['exclude'] is not None:
        exclude = [x.strip() for x in args['exclude'].split(',') if x and not x.isspace()]
        galaxies = galaxies.difference(exclude)

    for i in dataitems:
        m = search(i.name)
        if not m:
            print('skipped Test/Reduced-Data/{0}'.format(i.name))
            continue
        g = m.group(0)

        if g not in galaxies:
            continue

        print('processing {0}'.format(g))

        try:
            files = _getboxitems(i, r'kinematics_paperversion/more_files')
        except StopIteration:
            print('warning: missing data subdirectory ({0}/kinematics_paperversion/more_files)'.format(g))
            continue

        file_s2_folded_binspectra = next(x for x in files if x.name == g + '-s2-folded-binspectra.fits')
        file_s2_folded_fullgalaxy = next(x for x in files if x.name == g + '-s2-folded-fullgalaxy.fits')
        file_s2_folded_bininfo = next(x for x in files if x.name == g + '-s2-folded-bininfo.txt')
        file_s3_A_folded_temps_1 = next(x for x in files if x.name == g + '-s3-A-folded-temps-1.txt')
        file_s3_A_folded_temps_2 = next(x for x in files if x.name == g + '-s3-A-folded-temps-2.txt')
        file_s3_B_folded_moments = next(x for x in files if x.name == g + '-s3-B-folded-moments.txt')
        file_s4_folded_rprofiles = next(x for x in files if x.name == g + '-s4-folded-rprofiles.txt')
        file_s2_params = next(x for x in files if x.name == g + '_s2_params.txt')

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

            print('creating text file for {0}'.format(g))
            s2_folded_bininfo.seek(0)
            s3_B_folded_moments.seek(0)
            s4_folded_rprofiles.seek(0)
            joindata(s2_folded_bininfo, s3_B_folded_moments, s4_folded_rprofiles, data_output)

            print('creating fits file for {0}'.format(g))
            s2_folded_binspectra.seek(0)
            s2_folded_fullgalaxy.seek(0)
            s2_folded_bininfo.seek(0)
            s4_folded_rprofiles.seek(0)
            createfits(s2_folded_binspectra, s2_folded_fullgalaxy, s2_folded_bininfo, s3_B_folded_moments, s4_folded_rprofiles, fits_output)

            print('creating metadata file for {0}'.format(g))
            s2_folded_bininfo.seek(0)
            s3_A_folded_temps_1.seek(0)
            s3_A_folded_temps_2.seek(0)
            writemeta(s2_folded_bininfo, s3_A_folded_temps_1, s3_A_folded_temps_2, s2_params, meta_output)

            data_output.seek(0)
            fits_output.seek(0)
            meta_output.seek(0)

            print('uploading new data for {0}'.format(g))

            dataname = g + '.txt'
            try:
                dest = next(x for x in previousoutput if x.name == dataname)
                dest.update_contents_with_stream(data_output)
            except StopIteration:
                outputfolder.upload_stream(data_output, dataname)

            fitsname = g + '.fits'
            try:
                dest = next(x for x in previousoutput if x.name == fitsname)
                dest.update_contents_with_stream(fits_output)
            except StopIteration:
                outputfolder.upload_stream(fits_output, fitsname)

            metaname = g + '_meta.txt'
            try:
                dest = next(x for x in previousoutput if x.name == metaname)
                dest.update_contents_with_stream(meta_output)
            except StopIteration:
                outputfolder.upload_stream(meta_output, metaname)

if __name__ == '__main__':
    main()
