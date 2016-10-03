import re

def getstream(fname):
    opened = False
    try:
        if isinstance(fname, basestring):
            stream = open(fname, 'r')
            opened = True
        else:
            stream = iter(fname)
    except TypeError:
        raise TypeError('fname must be string to a valid path or iterable')
    return stream, opened

class metadata(object):
    def __init__(self, fname):
        self.data = {}
        rpair = re.compile(r'^# \s+(.+): (.+)$')

        stream, opened = getstream(fname)
        for line in stream:
            if line[0] != '#':
                break
            result = rpair.search(line)
            if not result:
                continue
            self.data[result.group(1)] = result.group(2)

        if opened:
            stream.close()

class header(object):
    def __init__(self, fname):
        section = -1
        self.metadata = {}
        self.comments = []

        rpair = re.compile(r'^# \s+(.+): (.+)$')

        stream, opened = getstream(fname)
        for line in stream:
            if line[0] != '#':
                break

            if line == '# Columns are as follows...\n' or line == '# Columns are as follows:\n':
                section = 1
                continue
            elif line == '# Metadata is as follows...\n' or line == '# Metadata is as follows:\n':
                section = 2
                continue
            elif line == '# Additional comments...\n' or line == '# Additional comments:\n':
                section = 3
                continue

            if section == 2:
                result = rpair.search(line)
                if not result:
                    section = 4

            if section == 1:
                self.columns = [x for x in line[1:].split()]
            elif section == 2:
                self.metadata[result.group(1)] = result.group(2)
            elif section == 3:
                self.comments.append(line[3:].rstrip())
            elif section == 4:
                self.comments.append(line[1:].strip())

        if opened:
            stream.close()