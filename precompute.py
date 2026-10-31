import json
from pathlib import Path

import numpy as np

from detector import clean_light_curve, search_periods


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
NASA_PERIODS = {
    "kepler8": 3.522498429,
    "kepler6": 3.234699282,
    "control": None,
}


def bin_daily(time, flux):
    day_bins = np.floor(time - time.min()).astype(int)
    counts = np.bincount(day_bins)
    time_sums = np.bincount(day_bins, weights=time)
    flux_sums = np.bincount(day_bins, weights=flux)
    occupied = counts > 0
    return {
        "time": (time_sums[occupied] / counts[occupied]).tolist(),
        "flux": (flux_sums[occupied] / counts[occupied]).tolist(),
    }


def downsample_periodogram(periods, scores, maximum_points=2000):
    if len(periods) <= maximum_points:
        return {"period": periods.tolist(), "score": scores.tolist()}

    period_chunks = np.array_split(periods, maximum_points)
    score_chunks = np.array_split(scores, maximum_points)
    selected_periods = []
    selected_scores = []
    for period_chunk, score_chunk in zip(period_chunks, score_chunks):
        peak_index = int(np.argmax(score_chunk))
        selected_periods.append(float(period_chunk[peak_index]))
        selected_scores.append(float(score_chunk[peak_index]))
    return {"period": selected_periods, "score": selected_scores}


def phase_folded(time, flux, period, transit_epoch, bin_count=48):
    phase_hours = (time - transit_epoch + period / 2) % period - period / 2
    phase_hours *= 24
    edges = np.linspace(-12, 12, bin_count + 1)
    bin_indices = np.digitize(phase_hours, edges) - 1
    inside = (bin_indices >= 0) & (bin_indices < bin_count)
    counts = np.bincount(bin_indices[inside], minlength=bin_count)
    flux_sums = np.bincount(
        bin_indices[inside], weights=flux[inside], minlength=bin_count
    )
    occupied = counts > 0
    centers = (edges[:-1] + edges[1:]) / 2
    return {
        "phase_hours": centers[occupied].tolist(),
        "flux": (flux_sums[occupied] / counts[occupied]).tolist(),
    }


def process_star(name, nasa_period):
    print(f"Processing {name}...")
    source_path = DATA_DIR / f"{name}.csv"
    data = np.genfromtxt(source_path, delimiter=",", names=True)
    raw_time = np.asarray(data["time"], dtype=float)
    raw_flux = np.asarray(data["flux"], dtype=float)
    valid = np.isfinite(raw_time) & np.isfinite(raw_flux) & (raw_flux > 0)
    raw_time = raw_time[valid]
    raw_flux = raw_flux[valid]
    order = np.argsort(raw_time)
    raw_time = raw_time[order]
    raw_flux = raw_flux[order]

    clean_time, clean_flux, _ = clean_light_curve(data["time"], data["flux"])
    periods, scores, result = search_periods(clean_time, clean_flux)
    print(f"  Trial periods: {len(periods)}")
    best_score = float(np.max(scores))
    aliases = result["alias_scores"]
    print(
        f"  Best score: {best_score:.3f} | "
        f"P/2 score: {aliases['half_period']} | "
        f"2P score: {aliases['double_period']}"
    )

    percent_difference = (
        abs(result["best_period"] - nasa_period) / nasa_period * 100
        if nasa_period is not None else None
    )
    output = {
        "name": name,
        "nasa_period": nasa_period,
        "result": result,
        "percent_difference_from_nasa": percent_difference,
        "raw_light_curve": bin_daily(raw_time, raw_flux),
        "cleaned_light_curve": bin_daily(clean_time, clean_flux),
        "periodogram": downsample_periodogram(periods, scores),
        "phase_folded": phase_folded(
            clean_time,
            clean_flux,
            result["best_period"],
            result["transit_epoch"],
        ),
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / f"{name}.json"
    output_path.write_text(json.dumps(output, separators=(",", ":")), encoding="utf-8")
    size_bytes = output_path.stat().st_size
    print(f"  JSON size: {size_bytes:,} bytes")
    if size_bytes >= 1_000_000:
        raise ValueError(f"{output_path} is not under 1 MB")


if __name__ == "__main__":
    for star_name, reference_period in NASA_PERIODS.items():
        process_star(star_name, reference_period)
    total_size = sum(
        (RESULTS_DIR / f"{name}.json").stat().st_size for name in NASA_PERIODS
    )
    print(f"Total JSON size: {total_size:,} bytes")
