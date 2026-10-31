I'm a 2nd year B.Tech AI & Data Science student, a beginner, building a portfolio project with your help. I want a working, deployed project in 1-2 days.

Project: Exoplanet Transit Detector

Goal:
A web app that takes a star's brightness data (light curve) from NASA's Kepler mission and detects the small, repeating dips that indicate a planet passing in front of its star. This is a numerical signal-processing project, not an "AI discovery system". Do not describe it that way.

What it should do:
- Let the user pick from 3 pre-saved stars: 2 with known planets (suggest Kepler-6 and Kepler-8, since their transits are deep and easy to detect; verify against actual downloaded data before committing) and 1 quiet control star in the Kepler field that is not a known planet candidate (verify it against the NASA Exoplanet Archive)
- Clean the data: remove invalid points, remove outliers with a robust median-based threshold, remove slow drift with a rolling-median baseline whose window is much longer than a transit (about a day) so the transit is not erased, then normalize
- Run a simplified box-fit (BLS-style) period search using NumPy: fold the data on each trial period, search for the lowest-brightness interval at several durations, score the signal against a flat baseline
- Report: best period, transit depth, estimated planet-to-star radius ratio (sqrt of depth), and a plain-English explanation
- Compare my detected period with the published NASA value (hardcoded, verified reference values with source) and show the difference
- For the control star, report "No significant transit detected in the analysed observations". Never claim "this star has no planet"

Plots (Chart.js in the browser):
1. Raw light curve
2. Cleaned light curve
3. Periodogram (signal score vs trial period), where a tall peak should appear at the detected period
4. Phase-folded transit

Design rules:
- This must NOT look like a dashboard: no card grid, no KPI tiles, no sidebar, no stat boxes. Make it a single scrolling page that tells the analysis in steps: 1) raw data, 2) cleaning, 3) period search, 4) folded transit, 5) NASA comparison. Each step has one chart and a short plain-English caption. Clean, simple, a bit like a lab notebook or a scientific article

Technical rules:
- Free tools only, no paid APIs, no database, no ML model
- Stack: Python, Flask, HTML/CSS/JavaScript. No React, Docker
- Detection uses only NumPy (scipy only if truly needed). Keep dependencies minimal
- Do NOT download NASA data at runtime. Give me a separate one-time script (scripts/download_data.py, using lightkurve) that I run locally to save each star's light curve as a small CSV in /data, committed to the repo. The deployed app only reads those CSVs
- Deployment: Vercel Hobby, from a GitHub repo. Use Vercel's zero-configuration Flask support: a Flask instance named `app` in app.py. Do not give me an old-style vercel.json with custom routes unless it is truly needed. No gunicorn
- Vercel's filesystem is read-only at runtime: never write files while the app runs
- Make sure /data is included in the Vercel deployment, and test that static files (CSS/JS) are served correctly. If they are not, tell me to move them to a public/ folder
- Keep API responses under 4.5 MB: bin or downsample light curves before sending to the browser
- Speed: restrict the trial-period range to roughly 1-10 days, bin the data to about 30-minute points, and benchmark the detector locally before deploying. It must finish within a few seconds
- Planned project structure: app.py, detector.py, requirements.txt, data/, scripts/download_data.py, templates/index.html, static/style.css, static/script.js

How I want you to help:
- I'm a beginner. You write the code, but explain each module in plain English before and after, so I can describe it myself later. Teach the astronomy concepts (light curve, transit, box fitting) before the code that uses them
- Build one module at a time. Test it, and wait for my confirmation before the next
- Explain errors before fixing them
- If any requirement is unrealistic or too complex for V1, say so directly. Do not agree with everything. Your goal is a working deployed project, not maximum complexity

Order of work:
1. First milestone: verify the three target stars and their published periods, and confirm the data downloads, with no detector code yet
2. Then: cleaning module, detector module (test against Kepler-6b's known period of about 3.235 days), Flask backend, frontend, NASA comparison, GitHub, Vercel deployment

V1 is successful if:
- It runs locally and on Vercel
- The detected period for a known-planet star matches the published value
- The control star shows a clearly weak or no detection
- The page reads as a step-by-step analysis, not a dashboard
- It can be finished in 1-2 days

Start with the first milestone only, then stop and wait for my confirmation.