import numpy as np
from scipy.optimize import curve_fit

def arcsec_to_kpc(x, D):
    """convert x to kpc from arcsec, given D (distance along LOS)"""
    return D*np.pi*x/(3600*180)

def sig_model(r,sig0=300,alpha=-0.1,beta=2,rb=10,
              r0=5,alphamax=2,betamax=2,rbmin=1,rbmax=1000):
    r = np.array(r)
    if rb < rbmin:
        sig0 = 1000
    elif rb>rbmax:
        sig0 = 1000
    elif np.abs(alpha) > alphamax:
        sig0 = 1000
    elif np.abs(beta) > alphamax:
        sig0 = 1000
    else:
        pass
    normalizer = ((rb/r0)**alpha)*(1 + r0/rb)**(alpha-beta)
    return sig0*(normalizer)*((r/rb)**alpha)*(1 + (r/rb))**(beta-alpha)

def fit_broken(rdata,sigdata,sigerrs,rb=5):
    model = lambda r,s,a,b: sig_model(r,sig0=s,alpha=a,rb=rb,beta=b)
    p0 = [250,-0.1,0.1]
    p, cov = curve_fit(model,rdata,sigdata,sigma=sigerrs,p0=p0)
    chisq = np.sum(((model(rdata,*p) - sigdata)/sigerrs)**2)/(len(rdata)-3)
    return p, chisq

def fit_pl(rdata,sigdata,sigerrs):
    model = lambda r,s,a: sig_model(r,sig0=s,alpha=a,beta=a)
    p0 = [250,-0.1]
    p, cov = curve_fit(model,rdata,sigdata,sigma=sigerrs,p0=p0)
    chisq = np.sum(((model(rdata,*p) - sigdata)/sigerrs)**2)/(len(rdata)-3)
    return p, chisq

def get_sigfits(moments, bininfo, d):
    r_kpc = arcsec_to_kpc(bininfo['r'],float(d)*1e3)
    items = {}
    pBR, chisqBR = fit_broken(r_kpc,moments['sigma'],moments['sigmaerr'])
    items['sigBR_sig0'] = pBR[0]
    items['sigBR_gamma1'] = pBR[1]
    items['sigBR_gamma2'] = pBR[2]
    items['sigBR_chisq'] = chisqBR
    pPL, chisqPL = fit_pl(r_kpc,moments['sigma'],moments['sigmaerr'])
    items['sigPL_sig0'] = pPL[0]
    items['sigPL_gamma'] = pPL[1]
    items['sigPL_chisq'] = chisqPL    
    return items

def get_h4fits(moments, bininfo, d):
    rphys = arcsec_to_kpc(bininfo['r'],float(d)*1e3)
    p = np.polyfit(np.log10(rphys),moments['h4'],1,w=1/moments['h4err'])
    items = {'h4grad':p[0], 'h4intercept':p[1]}
    return items
