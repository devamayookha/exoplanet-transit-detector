import json

for name in ["kepler8", "kepler6", "control"]:
    with open(f"data/results/{name}.json") as f:
        d = json.load(f)
    r = d["result"]
    print(f"{name}: period={r['best_period']:.6f} d | NASA={d['nasa_period']} | "
          f"diff={d['percent_difference_from_nasa']} % | depth={r['depth']*1e6:.0f} ppm | "
          f"duration={r['duration_hours']} h | significance={r['significance']:.1f}")