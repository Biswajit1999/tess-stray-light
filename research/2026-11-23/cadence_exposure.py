"""Exposure-window sensitivity diagnostics for TESS-like cadences."""
import numpy as np

def window_duty_cycle(start, stop, window_start, window_stop):
    """Union exposure coverage divided by externally defined observation window."""
    s, e = np.asarray(start, float), np.asarray(stop, float)
    if s.ndim != 1 or e.shape != s.shape or not s.size:
        raise ValueError("matching nonempty 1D intervals required")
    if not np.all(np.isfinite(s)) or not np.all(np.isfinite(e)) or np.any(e <= s):
        raise ValueError("invalid exposure intervals")
    if not np.isfinite(window_start) or not np.isfinite(window_stop) or window_stop <= window_start:
        raise ValueError("invalid observation window")
    intervals = sorted((max(x, window_start), min(y, window_stop)) for x,y in zip(s,e))
    covered = 0.
    right = window_start
    for a,b in intervals:
        if b <= a:
            continue
        covered += max(0., b-max(a,right))
        right = max(right,b)
    return covered/(window_stop-window_start)

def weighted_flux_mean(flux, sigma, exposure, retained):
    """Inverse-variance and exposure weighted mean; independent-error standard error."""
    f, s, t, keep = map(np.asarray, (flux, sigma, exposure, retained))
    if not (f.ndim == s.ndim == t.ndim == keep.ndim == 1 and f.size == s.size == t.size == keep.size):
        raise ValueError("one-dimensional matching arrays required")
    if not (np.all(np.isfinite(f)) and np.all(np.isfinite(s)) and np.all(np.isfinite(t))):
        raise ValueError("finite arrays required")
    if np.any(s <= 0) or np.any(t <= 0) or keep.dtype != np.dtype(bool) or not np.any(keep):
        raise ValueError("positive sigma/exposure and nonempty boolean mask required")
    w = t[keep]/s[keep]**2
    mean = np.sum(w*f[keep])/np.sum(w)
    # For independent heteroscedastic measurements, Var(weighted mean) = sum(w_i^2 sigma_i^2)/(sum w_i)^2.
    se = np.sqrt(np.sum(w*w*s[keep]**2))/np.sum(w)
    return float(mean), float(se)
