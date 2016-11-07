import argparse
import os
import re

def main():
    parser = argparse.ArgumentParser(
        description='Creates data table from MASSIVE survey public data.'
    )

    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Path to public data folder.'
    )

    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Path to destination directory.'
    )

    parser.add_argument(
        '-p', '--paperonly',
        action='store_true',
        help='Creates table with only galaxies from paper V.'
    )

    args = vars(parser.parse_args())

    createtable(
        args['input'],
        args['output'],
        False,
        args['paperonly']
    )

    createtable(
        args['input'],
        args['output'],
        True,
        args['paperonly']
    )

def resultlen(data, fmt):
    if '.' in fmt:
        pos = data.find('.')
        if pos == -1:
            return len(data)
        return pos + int(fmt[1]) + 1
    return len(data)

def fixkey(key, g2type):
    if key == 'sig0':
        return 'sig' + g2type + 's0'
    if key == 'gam1':
        val = 'sig' + g2type + 'g1'
        if val == 'sigPLg1':
            val = 'sigPLg2'
        return val
    if key == 'gam2':
        return 'sig' + g2type + 'g2'
    return key

def createtable(src, dest, alt, paperonly):
    search = re.compile(r'^[A-Z]+\d+$').search
    dirs = os.listdir(src)
    galaxies = set(m.group(0) for m in (search(f) for f in dirs) if m)
    #data = {g: readmeta(os.path.join(src, g, g + '-folded-misc.txt')) for g in galaxies}

    papergalaxies = [
        'NGC0057', 'NGC0315', 'NGC0383', 'NGC0410', 'NGC0507', 'NGC0533', 'NGC0545', 'NGC0547',
        'NGC0741', 'NGC0777', 'NGC1016', 'NGC1060', 'NGC1132', 'NGC1129', 'NGC1272', 'NGC1600',
        'NGC2256', 'NGC2274', 'NGC2320', 'NGC2340', 'NGC2693', 'NGC2783', 'NGC2832', 'NGC2892',
        'NGC3158', 'NGC3805', 'NGC3842', 'NGC4073', 'NGC4472', 'NGC4555', 'NGC4839', 'NGC4874',
        'NGC4889', 'NGC4914', 'NGC5129', 'UGC10918', 'NGC7242', 'NGC7265', 'NGC7426', 'NGC7436',
        'NGC7556'
    ]

    if paperonly:
        galaxies = galaxies.intersection(papergalaxies)

    data = {g: readmeta(os.path.join(src, g, g + '-folded-misc.txt')) for g in galaxies}

    if alt:
        columns = [
            ('galaxy', ''),
            ('mhalo', ''),
            ('sigtype', ''),
            ('g2type', ''),
            ('sig0', ''),
            ('gam1', ''),
            ('gam2', ''),
            ('h3avg', ''),
            ('h3avge', ''),
            ('h4avg', ''),
            ('h4avge', ''),
            ('h5avg', ''),
            ('h5avge', ''),
            ('h6avg', ''),
            ('h6avge', ''),
            ('h3vgrad', ''),
            ('h3vgrade', ''),
            ('h4rgrad', '')
        ]
    else:
        columns = [
            ('galaxy', ''),
            ('ra', '.4f'),
            ('dec', '.4f'),
            ('d', '.1f'),
            ('mk', '.2f'),
            ('re', '.1f'),
            ('eps', '.2f'),
            ('pa', '.1f'),
            ('rmax', '.2f'),
            ('lam', '.2f'),
            ('sigc', '.0f'),
            ('sigavg', '.0f'),
            ('envN', '.0f')
        ]

    cols, fmts = zip(*columns)
    #widths = [max(len(data[g][key]) for g in data) for key in cols]

    if alt:
        widths = [max([resultlen(data[g][fixkey(k, data[g]['g2type'])], v) for g in data] + [len(k)]) for k, v in columns]
    else:
        widths = [max([resultlen(data[g][k], v) for g in data] + [len(k)]) for k, v in columns]

    hdrfmt = '  '.join('{{:>{0}}}'.format(i) for i in widths)
    fmt = '  '.join('{{:>{0}{1}}}'.format(i, x) for i, x in zip(widths, fmts))

    #widths = [max(len(data[g][key]) for g in data) for key in cols]
    #fmt = '  '.join('{{:>{0}}}'.format(x) for x in widths)

    fname = 'table{}{}.txt'.format('-paper' if paperonly else '-all', '-extras' if alt else '')

    with open(os.path.join(dest, fname), 'w') as out:
        out.write('# ' + hdrfmt.format(*cols) + '\n')

        if 'pa' in cols:
            for gal in sorted(galaxies):
                pa = data[gal]['pa']
                pakin = data[gal]['pakin']
                if pa != pakin:
                    out.write('#  {0} has pakin ({1}) that doesn\'t match pa ({2})\n'.format(gal, pakin, pa))

        for gal in sorted(galaxies):
            if alt:
                line = (float(data[gal][fixkey(c, data[gal]['g2type'])]) if len(f) > 1 and f[-1] == 'f' else data[gal][fixkey(c, data[gal]['g2type'])] for c, f in columns)
            else:
                line = (float(data[gal][c]) if len(f) > 1 and f[-1] == 'f' else data[gal][c] for c, f in columns)
            out.write('  ' + fmt.format(*line) + '\n')

def readmeta(path):
    data = {}
    with open(path, 'r') as metadata:
        for line in metadata:
            if line[0] == '#':
                continue
            key, val = line.split()
            data[key.strip()] = val.strip()
    return data

if __name__ == '__main__':
    main()
