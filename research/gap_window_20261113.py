"""Gap-aware pair counts and autocorrelation; conditional synthetic diagnostic."""
import math
def pairwise_lags(cadences, flux, max_lag):
    if len(cadences)!=len(flux) or len(set(cadences))!=len(cadences) or max_lag<1:
        raise ValueError("invalid cadences")
    if not all(isinstance(k,int) for k in cadences) or not all(math.isfinite(v) for v in flux):
        raise ValueError("invalid values")
    d=dict(zip(cadences,flux))
    result=[]
    for lag in range(1,max_lag+1):
        p=[(v,d[k+lag]) for k,v in d.items() if k+lag in d]
        n=len(p)
        if n<2: result.append((lag,n,None));continue
        a=sum(x for x,y in p)/n;b=sum(y for x,y in p)/n
        vx=sum((x-a)**2 for x,y in p);vy=sum((y-b)**2 for x,y in p)
        r=sum((x-a)*(y-b) for x,y in p)/math.sqrt(vx*vy) if vx>0 and vy>0 else None
        result.append((lag,n,r))
    return result
def effective_n(n, rhos):
    if n<2: raise ValueError("n must be >=2")
    tau=1.
    for r in rhos:
        if r is None or not math.isfinite(r) or r<=0: break
        if r>1: raise ValueError("correlation above one")
        tau+=2*r
    return n/tau
