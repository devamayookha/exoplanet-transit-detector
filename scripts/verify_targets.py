import csv
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import lightkurve as lk

# NASA reference information
TARGETS = {
    "Kepler-6": {
        "kic": 10874614,
        "period": 3.234699282,
        "filename": "kepler6.csv"
    },
    "Kepler-8": {
        "kic": 6922244,
        "period": 3.522498429,
        "filename": "kepler8.csv"
    }
}

DATA_DIR = Path("data")
PLOT_DIR = Path("verification_plots")

DATA_DIR.mkdir(exist_ok=True)
PLOT_DIR.mkdir(exist_ok=True)


def verify_target(name, details):

    kic = details["kic"]
    reference_period = details["period"]

    print("\n" + "=" * 55)
    print(f"TARGET: {name}")
    print(f"KIC: {kic}")
    print(f"NASA period: {reference_period:.9f} days")
    print("=" * 55)

    # Search official Kepler long-cadence observations
    search = lk.search_lightcurve(
        f"KIC {kic}",
        mission="Kepler",
        author="Kepler",
        exptime=1800
    )

    if len(search) == 0:
        print("ERROR: No matching light curves found.")
        return None

    print(f"\nAvailable data products: {len(search)}")
    print(search)

    # Download all available quarters
    collection = search.download_all(
        quality_bitmask="default",
        flux_column="pdcsap_flux"
    )

    all_times = []
    all_fluxes = []

    print("\nQUARTER DETAILS")

    for lc in collection:

        time = np.asarray(lc.time.value, dtype=float)
        flux = np.asarray(lc.flux.value, dtype=float)

        # Remove invalid observations
        valid = (
            np.isfinite(time) &
            np.isfinite(flux) &
            (flux > 0)
        )

        time = time[valid]
        flux = flux[valid]

        if len(time) == 0:
            continue

        # Normalize this quarter independently
        median_flux = np.median(flux)

        if median_flux <= 0:
            continue

        normalized_flux = flux / median_flux

        quarter = getattr(lc, "quarter", "Unknown")

        gaps = np.sum(np.diff(time) > 0.1)

        print(
            f"Quarter {quarter}: "
            f"{len(time)} valid points | "
            f"{time.min():.2f} to {time.max():.2f} BKJD | "
            f"{gaps} large gaps"
        )

        all_times.extend(time)
        all_fluxes.extend(normalized_flux)

    if not all_times:
        print("ERROR: No usable observations.")
        return None

    # Combine and sort observations
    times = np.asarray(all_times)
    fluxes = np.asarray(all_fluxes)

    order = np.argsort(times)
    times = times[order]
    fluxes = fluxes[order]

    # Remove duplicate timestamps
    unique = np.concatenate(
        ([True], np.diff(times) > 1e-8)
    )

    times = times[unique]
    fluxes = fluxes[unique]

    print("\nCOMBINED DATA SUMMARY")
    print(f"Valid observations: {len(times)}")
    print(f"Start time: {times.min():.6f} BKJD")
    print(f"End time: {times.max():.6f} BKJD")
    print(f"Total baseline: {np.ptp(times):.2f} days")

    # Save provisional CSV with exactly two columns
    filename = DATA_DIR / details["filename"]

    with open(filename, "w", newline="") as file:

        writer = csv.writer(file)

        writer.writerow(["time", "flux"])

        for t, f in zip(times, fluxes):
            writer.writerow([
                f"{t:.6f}",
                f"{f:.7f}"
            ])

    size = filename.stat().st_size

    print(f"\nCSV saved: {filename}")
    print(f"CSV size: {size:,} bytes")
    print(f"CSV size: {size / 1024:.2f} KB")

    # Generate a local inspection plot
    plt.figure(figsize=(13, 4))

    plt.plot(times, fluxes, ".", markersize=1)

    plt.xlabel("Time (BKJD)")
    plt.ylabel("Normalized Flux")
    plt.title(f"{name} - Combined Light Curve")

    plt.grid(alpha=0.25)
    plt.tight_layout()

    plot_file = PLOT_DIR / f"{name.lower().replace('-', '')}.png"

    plt.savefig(plot_file, dpi=130)
    plt.close()

    print(f"Preview plot: {plot_file}")

    # Show period and alias reference values
    print("\nPERIOD ALIAS CHECK REFERENCES")
    print(f"P/2: {reference_period / 2:.6f} days")
    print(f"P:   {reference_period:.6f} days")
    print(f"2P:  {reference_period * 2:.6f} days")

    return size


def main():

    total_size = 0

    for name, details in TARGETS.items():

        size = verify_target(name, details)

        if size is not None:
            total_size += size

    print("\n" + "=" * 55)
    print("TOTAL DATA SIZE")
    print(f"{total_size:,} bytes")
    print(f"{total_size / 1024:.2f} KB")
    print("=" * 55)

    print("\nControl star has NOT been selected.")
    print("We will select it after inspecting candidate light curves.")


if __name__ == "__main__":
    main()