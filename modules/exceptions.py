
def checkforexceptions(items,galaxy):
    if not galaxy in _exceptions: return items
    print 'Making manual exceptions for {0}:'.format(galaxy)
    edict = _exceptions[galaxy]
    for key in edict:
        if not key in items: continue # don't add the item if not already there
        print ' changing {} from {} to {}'.format(key,items[key],edict[key])
        items[key] = edict[key]
    return items

_exceptions = {
    'NGC1129': {'pa': 46.2}, # bininfo contains correct pa_kin, 0 degrees
    'NGC4874': {'pa': 40.6} # bininfo contains correct pa_kin, 145 degrees
}

# Here are some additional notes about possible exceptions not needed after all:
# NGC0545: M_K is correct (uses the 547 value) in bininfo already
# NGC4472: should have Re = 177.0 and does already
# NGC1129: epsilon should be 0.15 and is already
# NGC4472: epsilon should be 0.17 and is already
