import lightkurve as lk

for name in ["Kepler-6", "Kepler-8"]:
    result = lk.search_lightcurve(name, mission="Kepler", author="Kepler", cadence="long")
    print(name, "->", len(result), "files found")
    print(result)