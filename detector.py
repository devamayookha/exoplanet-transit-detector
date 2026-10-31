import numpy as np


def _rolling_median(time, flux, window_days=1.0):
    baseline = np.empty_like(flux, dtype=float)
    half_window = window_days / 2
    start = 0

    while start < len(time):
        end = start + 1
        while end < len(time) and time[end] - time[end - 1] <= 0.5:
            end += 1

        segment_time = time[start:end]
        segment_flux = flux[start:end]
        for index, value in enumerate(segment_time):
            left = np.searchsorted(segment_time, value - half_window, side="left")
            right = np.searchsorted(segment_time, value + half_window, side="right")
            baseline[start + index] = np.median(segment_flux[left:right])
        start = end

    return baseline


def clean_light_curve(time, flux):
    time = np.asarray(time, dtype=float)
    flux = np.asarray(flux, dtype=float)
    if time.ndim != 1 or flux.ndim != 1 or len(time) != len(flux):
        raise ValueError("time and flux must be one-dimensional arrays of equal length")

    valid = np.isfinite(time) & np.isfinite(flux) & (flux > 0)
    time = time[valid]
    flux = flux[valid]
    order = np.argsort(time)
    time = time[order]
    flux = flux[order]

    if len(time) == 0:
        raise ValueError("the light curve has no valid points")

    median_flux = np.median(flux)
    robust_scatter = 1.4826 * np.median(np.abs(flux - median_flux))
    if robust_scatter > 0:
        keep = flux <= median_flux + 5 * robust_scatter
        time = time[keep]
        flux = flux[keep]

    if len(time) == 0:
        raise ValueError("outlier clipping removed every light-curve point")

    baseline = _rolling_median(time, flux)
    usable = np.isfinite(baseline) & (baseline > 0)
    time = time[usable]
    flux = flux[usable]
    baseline = baseline[usable]

    if len(time) == 0:
        raise ValueError("could not estimate a positive rolling baseline")

    return time, flux / baseline, baseline


if __name__ == "__main__":
    import time as timer
    from pathlib import Path

    for name in ["kepler8", "kepler6", "control"]:
        path = Path(__file__).parent / "data" / f"{name}.csv"
        data = np.genfromtxt(path, delimiter=",", names=True)
        t, f = data["time"], data["flux"]

        start = timer.time()
        ct, cf, base = clean_light_curve(t, f)
        elapsed = timer.time() - start
        valid_flux = f[np.isfinite(f) & (f > 0)]
        before_depth = 1 - np.min(valid_flux) / np.median(valid_flux)
        after_depth = 1 - np.min(cf)

        print(f"{name}: removed {len(t) - len(ct)} points | "
              f"points below 0.995: before {int(np.sum(f < 0.995))}, "
              f"after {int(np.sum(cf < 0.995))} | "
              f"deepest dip: before {before_depth * 1e6:.0f} ppm, "
              f"after {after_depth * 1e6:.0f} ppm | {elapsed:.1f}s")
