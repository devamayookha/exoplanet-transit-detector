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


def search_periods(time, flux, period_min=1.0, period_max=10.0):
    time = np.asarray(time, dtype=float)
    flux = np.asarray(flux, dtype=float)
    if time.ndim != 1 or flux.ndim != 1 or len(time) != len(flux):
        raise ValueError("time and flux must be one-dimensional arrays of equal length")

    valid = np.isfinite(time) & np.isfinite(flux)
    time = time[valid]
    flux = flux[valid]
    order = np.argsort(time)
    time = time[order]
    flux = flux[order]
    if len(time) < 2:
        raise ValueError("at least two valid light-curve points are required")
    if not (0 < period_min < period_max):
        raise ValueError("period limits must satisfy 0 < period_min < period_max")

    observation_baseline = time[-1] - time[0]
    if observation_baseline <= 0:
        raise ValueError("the light curve must span a positive time interval")

    transit_duration_days = 3.0 / 24.0
    period_factor = 1.0 + transit_duration_days / (2 * observation_baseline)
    trial_periods = []
    period = float(period_min)
    while period <= period_max:
        trial_periods.append(period)
        period *= period_factor
    periods = np.asarray(trial_periods)
    trial_frequencies = 1.0 / periods

    cadence_days = 0.5 / 24.0
    durations_hours = np.array([1.5, 3.0, 4.5, 6.0])
    durations_bins = np.maximum(1, np.rint(durations_hours / 0.5).astype(int))
    scores = np.zeros(len(periods), dtype=float)
    best_depth = 0.0
    best_score = -np.inf
    best_duration_hours = float(durations_hours[0])
    best_epoch = float(time[0])
    robust_noise = 1.4826 * np.median(np.abs(flux - np.median(flux)))
    if robust_noise <= 0:
        raise ValueError("the cleaned flux must have nonzero robust scatter")

    for period_index, period in enumerate(periods):
        bin_count = max(12, int(np.ceil(period / cadence_days)))
        phase = np.remainder(time * trial_frequencies[period_index], 1.0)
        phase_bins = np.minimum((phase * bin_count).astype(int), bin_count - 1)
        bin_points = np.bincount(phase_bins, minlength=bin_count)
        bin_flux_sum = np.bincount(phase_bins, weights=flux, minlength=bin_count)

        # Three copies make every circular phase window a contiguous slice.
        extended_points = np.tile(bin_points, 3)
        extended_flux = np.tile(bin_flux_sum, 3)
        cumulative_points = np.concatenate(([0], np.cumsum(extended_points)))
        cumulative_flux = np.concatenate(([0.0], np.cumsum(extended_flux)))
        starts = np.arange(bin_count, 2 * bin_count)
        best_period_score = -np.inf
        period_candidate = None

        for duration_hours, width in zip(durations_hours, durations_bins):
            ends = starts + width
            in_count = cumulative_points[ends] - cumulative_points[starts]
            in_sum = cumulative_flux[ends] - cumulative_flux[starts]
            out_count = len(time) - in_count
            usable = (in_count > 0) & (out_count > 0)
            if not np.any(usable):
                continue

            in_mean = in_sum[usable] / in_count[usable]
            out_mean = (np.sum(flux) - in_sum[usable]) / out_count[usable]
            depth = out_mean - in_mean
            score = depth / (
                robust_noise
                * np.sqrt(1.0 / in_count[usable] + 1.0 / out_count[usable])
            )
            local_index = int(np.argmax(score))
            if score[local_index] > best_period_score:
                usable_starts = starts[usable]
                start_bin = usable_starts[local_index] % bin_count
                center_phase = ((start_bin + width / 2) / bin_count) % 1.0
                best_period_score = float(score[local_index])
                period_candidate = (
                    max(0.0, float(depth[local_index])),
                    float(duration_hours),
                    center_phase,
                )

        if period_candidate is not None:
            scores[period_index] = best_period_score
            if best_period_score > best_score:
                best_score = best_period_score
                best_depth, best_duration_hours, best_phase = period_candidate
                best_period = float(period)
                first_phase = np.remainder(time[0] / period, 1.0)
                best_epoch = float(
                    time[0] + np.mod(best_phase - first_phase, 1.0) * period
                )

    score_scatter = np.std(scores)
    significance = (
        float((np.max(scores) - np.median(scores)) / score_scatter)
        if score_scatter > 0 else 0.0
    )
    best_index = int(np.argmax(scores))
    best_period = float(periods[best_index])

    def score_near(target_period):
        if target_period < period_min or target_period > period_max:
            return None
        return float(scores[np.argmin(np.abs(periods - target_period))])

    result = {
        "best_period": best_period,
        "depth": best_depth,
        "duration_hours": best_duration_hours,
        "transit_epoch": best_epoch,
        "significance": significance,
        "alias_scores": {
            "half_period": score_near(best_period / 2),
            "double_period": score_near(best_period * 2),
        },
    }
    return periods, scores, result


if __name__ == "__main__":
    import time as timer
    from pathlib import Path

    nasa_periods = {"kepler8": 3.5225, "kepler6": 3.2347, "control": None}
    for name in ["kepler8", "kepler6", "control"]:
        path = Path(__file__).parent / "data" / f"{name}.csv"
        data = np.genfromtxt(path, delimiter=",", names=True)
        t, f = data["time"], data["flux"]

        ct, cf, base = clean_light_curve(t, f)
        start = timer.time()
        periods, scores, result = search_periods(ct, cf)
        elapsed = timer.time() - start
        nasa_period = nasa_periods[name]
        if nasa_period is None:
            reference = "N/A"
            difference = "N/A"
        else:
            percent_difference = abs(result["best_period"] - nasa_period) / nasa_period * 100
            reference = f"{nasa_period:.4f} days"
            difference = f"{percent_difference:.2f}%"
        print(f"{name}: best_period={result['best_period']:.6f} days | "
              f"NASA={reference} | difference={difference} | "
              f"significance={result['significance']:.2f} | "
              f"search={elapsed:.2f}s | trials={len(periods)}")
