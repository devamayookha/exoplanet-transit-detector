import csv
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import lightkurve as lk

CANDIDATES = [6922277, 6922204, 7007617, 6836484]
REFERENCE = 6922244  # Kepler-8, for comparison

OUT = Path("data/candidates")
PLOTS = Path("verification_plots")
OUT.mkdir(parents=True, exist_ok=True)
PLOTS.mkdir(exist_ok=True)


def load_star(kic):
    search = lk.search_lightcurve(f"KIC {kic}", mission="Kepler",
                                  author="Kepler", exptime=1800)
    collection = search.download_all(quality_bitmask="default",
                                     flux_column="pdcsap_flux")
    times, fluxes = [], []
    for lc in collection:
        t = np.asarray(lc.time.value, dtype=float)
        f = np.asarray(lc.flux.value, dtype=float)
        ok = np.isfinite(t) & np.isfinite(f) & (f > 0)
        t, f = t[ok], f[ok]
        if len(t) == 0:
            continue
        times.extend(t)
        fluxes.extend(f / np.median(f))
    times, fluxes = np.asarray(times), np.asarray(fluxes)
    order = np.argsort(times)
    return times[order], fluxes[order]


def summarize(kic):
    t, f = load_star(kic)
    # robust scatter (not thrown off by outliers), in parts per million
    noise_ppm = 1.4826 * np.median(np.abs(f - np.median(f))) * 1e6
    deep_dips = int(np.sum(f < 0.99))   # points more than 1% below normal
    print(f"KIC {kic}: {len(t)} points | noise {noise_ppm:.0f} ppm | "
          f"points below 0.99: {deep_dips}")

    with open(OUT / f"{kic}.csv", "w", newline="") as file:
        w = csv.writer(file)
        w.writerow(["time", "flux"])
        for a, b in zip(t, f):
            w.writerow([f"{a:.6f}", f"{b:.7f}"])

    plt.figure(figsize=(13, 4))
    plt.plot(t, f, ".", markersize=1)
    plt.ylim(0.985, 1.015)
    plt.title(f"KIC {kic}")
    plt.xlabel("Time (BKJD)")
    plt.ylabel("Normalized Flux")
    plt.tight_layout()
    plt.savefig(PLOTS / f"candidate_{kic}.png", dpi=110)
    plt.close()


if __name__ == "__main__":
    print("Reference:")
    summarize(REFERENCE)
    print("\nCandidates:")
    for kic in CANDIDATES:
        summarize(kic)
