<div align="center">

# 🪐 Exoplanet Transit Detector

**Finding planets in the shadow they cast on their stars**

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Open_the_notebook-28665d?style=for-the-badge)](https://exoplanet-transit-detector.vercel.app/)

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-FF6384?style=flat-square&logo=chartdotjs&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white)
![Data](https://img.shields.io/badge/Data-NASA_Kepler-0B3D91?style=flat-square)

</div>

---

## 🌟 What it does

When a planet passes in front of its star, the star dims slightly. This project looks for that **repeating dip** in four years of NASA Kepler observations and reports the planet's orbital period, the transit depth, and a rough size estimate.

The web page walks through the analysis in five steps, like a short lab notebook: raw data → cleaning → period search → folded transit → comparison with NASA.

## 🔭 Stars analysed

| Star | Role |
|---|---|
| 🟢 **Kepler-8** | Known planet (Kepler-8 b) |
| 🟢 **Kepler-6** | Known planet (Kepler-6 b) |
| ⚪ **KIC 6922277** | Control: quiet Kepler-field star, not a known planet candidate |

## ✅ Results

| Star | Detected period | NASA period | Difference | Significance |
|---|---|---|---|---|
| Kepler-8 | 3.522553 d | 3.522498 d | **0.0015%** | 43.7 |
| Kepler-6 | 3.234718 d | 3.234699 d | **0.0006%** | 40.8 |
| Control | 9.361 d *(noise)* | none | n/a | 5.9 |

Both planet stars peak at the published period. The control's strongest peak is ordinary noise, so **no transit was detected** in these observations. That is not proof the star has no planet.

## ⚙️ How it works

1. 📡 **Data.** Kepler long-cadence light curves (30-minute samples, about 4 years, 18 quarters), downloaded once with Lightkurve and saved as small CSV files.
2. 🧹 **Cleaning.** Invalid points are dropped. Only unusually *high* outliers are removed, because a transit is a dip. A rolling median about 1 day wide removes slow drift without erasing the transit, and the flux is divided by it. More than 99% of the transit points survived cleaning for both planet stars.
3. 🔎 **Period search.** A simplified box-fit search written in NumPy. About 54,000 trial periods between 1 and 10 days, spaced so a true period cannot be skipped. For each one, the data is folded and a box-shaped dip is slid across it at several durations. The score is how far the dimmest window stands out from the noise.
4. 🔁 **Aliases.** A true period also lights up at half and double its value. The page shows the P/2 and 2P scores, which come out at roughly 65-70% of the main peak, so the real period wins clearly.
5. 📉 **Folding.** Observations are folded on the best period so repeated transits stack into one visible dip.

The live page only reads **precomputed results** from `data/results/`. The heavy search runs offline in `precompute.py`, so the page is fast and does not need NumPy.

## ⚠️ Limitations

- 📏 **Depth is underestimated.** A box model averages over the sloped edges of a transit, so the table's depth reads lower than the dip you can see in the folded curve. The radius ratio (square root of depth) is therefore a simplified estimate.
- 🚫 **A control is not proof of "no planet".** A planet could exist without crossing our line of sight, or be too shallow for this method.
- 💾 **Results are precomputed.** The page does not run the search live.
- 🪐 **Only three stars.** The method was validated on two deep transits from large planets. Small, shallow planets would be much harder.
- 🔢 **Significance is a ratio, not a probability.** It compares the best score with the scatter of all scores.

## 🏃 Run locally

```bash
git clone https://github.com/devamayookha/exoplanet-transit-detector.git
cd exoplanet-transit-detector
pip install flask
python app.py
```

Then open http://127.0.0.1:5000.

To regenerate the data and results (needs internet, takes a few minutes):

```bash
pip install lightkurve numpy matplotlib
python scripts/verify_targets.py   # downloads Kepler-6 and Kepler-8
python precompute.py               # cleans, searches, writes data/results/*.json
python check_results.py            # prints detected vs NASA periods
```

## 🗂️ Project structure

```
app.py               Flask app: serves the page and the JSON results
detector.py          cleaning and period-search code
precompute.py        runs the detector, writes data/results/*.json
check_results.py     prints the validation numbers
data/                Kepler light curves (CSV) and results (JSON)
scripts/             data download and control-star selection
templates/, static/  the five-step web page
```

## 🔮 Possible next steps

- Fit a proper transit shape for a better depth and radius ratio
- Add more stars, including shallower planets
- Add a live search with a precomputed fast path
- Rewrite the period search in C++ and measure the speed-up

## 🙏 Data and credits

Kepler data from the Mikulski Archive for Space Telescopes (MAST). Reference periods from the NASA Exoplanet Archive.

---

<div align="center">

**B R Devamayookha**
[GitHub](https://github.com/devamayookha) · [LinkedIn](https://linkedin.com/in/b-r-devamayookha-627305375)

</div>