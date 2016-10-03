from collections import OrderedDict
import numpy as np

# This is pasted from massivepy.postprocess
def group_bins(bindata,n0=3):
    """
    Group bins into annuli. Does the obvious thing for outer annuli.
    Also groups the center single-fiber bins into annuli of approximately
    equal radius, based on having n0 as the number of bins in the "first"
    (center) annulus, and having the total number of bins enclosed in the nth
    annulus scale like n^2.
    E.g. for n0=3 the total number of bins enclosed goes 3, 12, 27, 48 etc,
    so the number in each annulus goes 3, 9, 15, 21, etc.
    Note that the final annulus in the center region will have slightly more
    or fewer bins/fibers than this.
    Returns a list of arrays, each containing the bin indexes for one annulus.
    NOTE, this requires the center bins to be sorted!!
    """
    n_singlebins = np.sum(np.isnan(bindata['rmin']))
    if n_singlebins==0:
        ii_splits = []
    else:
        n_centerannuli = int(np.rint(np.sqrt(n_singlebins/float(n0))))
        ii_splits = list(np.array(range(1,n_centerannuli))**2 * n0)
        ii_splits.append(n_singlebins)
    jj_annuli = np.nonzero(np.diff(bindata['rmin'][n_singlebins:]))[0]
    ii_splits.extend(n_singlebins+jj_annuli+1)
    return np.split(range(len(bindata)),ii_splits)

def get_re_averages(moments, bininfo, re):
    # get fancy averages and error bars, a la sigma_e
    re = float(re)
    bin_groups, bin_groups_en = group_bins(bininfo), []
    dt = {'names':['r','sigma','sigmaerr','h3','h3err','h4','h4err',
                   'h5','h5err','h6','h6err'],'formats':11*['f8']}
    endata = np.zeros(len(bin_groups),dtype=dt)
    for j, group in enumerate(bin_groups):
        bin_groups_en.extend(group)
        bd = bininfo[np.array(bin_groups_en)]
        bm = moments[np.array(bin_groups_en)]
        lum = bd['flux']*bd['nfibers']
        sqrtN = np.sqrt(len(lum))
        if all(np.isnan(bd['rmax'])): endata['r'][j] = np.max(bd['r'])
        else: endata['r'][j] = bd['rmax'][-1]
        for key in ['sigma','h3','h4','h5','h6']:
            endata[key][j] = np.average(bm[key],weights=lum)
            endata[key+'err'][j] = np.average(bm[key+'err'],weights=lum)/sqrtN
    items = OrderedDict()
    for key in ['sigma','h3','h4','h5','h6']:
        k = 'sig' if key == 'sigma' else key
        items[k+'avg'] = np.interp(re,endata['r'],endata[key])
        items[k+'avge'] = np.interp(re,endata['r'],endata[key+'err'])
    return items
