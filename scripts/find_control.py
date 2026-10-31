import urllib.request
import lightkurve as lk

# 1. Find Kepler long-cadence stars near Kepler-8
result = lk.search_lightcurve("KIC 6922244", mission="Kepler",
                              author="Kepler", exptime=1800, radius=900)
names = [str(n) for n in result.table["target_name"]]

counts = {}
for n in names:
    kic = int(n.replace("kplr", ""))
    counts[kic] = counts.get(kic, 0) + 1

print("Stars found nearby:", len(counts))

# 2. Ask NASA which of these are planet candidates (KOIs)
ids = ",".join(str(k) for k in counts)
url = ("https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query="
       f"select+kepid+from+cumulative+where+kepid+in+({ids})&format=csv")
with urllib.request.urlopen(url) as r:
    lines = r.read().decode().strip().split("\n")[1:]
koi_ids = {int(x) for x in lines if x.strip()}

# 3. Print stars that are NOT candidates and have lots of data
print("\nControl star candidates (not in NASA's candidate list):")
for kic, n in sorted(counts.items(), key=lambda x: -x[1]):
    if kic not in koi_ids and kic != 6922244:
        print(f"KIC {kic}: {n} quarters")
