(() => {
  "use strict";

  const selector = document.getElementById("star-select");
  const status = document.getElementById("load-status");
  const charts = {};

  const DEFAULT_PERIOD_CAPTION =
    "The search folds observations across trial periods and scores how strongly " +
    "a short dim interval stands out.";
  const DEFAULT_FOLDED_CAPTION =
    "Mean brightness in phase bins around the estimated transit midpoint. " +
    "Every star is drawn on the same vertical scale so the dips can be compared.";

  const chartColors = {
    line: "#28665d",
    point: "rgba(40, 102, 93, 0.55)",
    highlight: "#b6533c",
    grid: "rgba(38, 51, 47, 0.10)",
    text: "#62706a",
  };

  function scatterChart(canvasId, label, points, xTitle, yTitle, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (charts[canvasId]) {
      charts[canvasId].destroy();
    }

    charts[canvasId] = new Chart(canvas, {
      type: "scatter",
      data: {
        datasets: [{
          label,
          data: points,
          showLine: options.showLine !== false,
          borderColor: chartColors.line,
          backgroundColor: chartColors.point,
          borderWidth: 1.5,
          pointRadius: options.pointRadius ?? 1.5,
          pointHoverRadius: 3,
          tension: 0,
        }],
      },
      options: {
        animation: false,
        maintainAspectRatio: false,
        normalized: true,
        parsing: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) =>
                `${xTitle}: ${context.parsed.x.toFixed(3)}, ${yTitle}: ${context.parsed.y.toFixed(6)}`,
            },
          },
        },
        scales: {
          x: {
            type: "linear",
            min: options.xMin,
            title: { display: true, text: xTitle, color: chartColors.text },
            grid: { color: chartColors.grid },
            ticks: { color: chartColors.text, maxTicksLimit: 9 },
          },
          y: {
            min: options.yMin,
            max: options.yMax,
            title: { display: true, text: yTitle, color: chartColors.text },
            grid: { color: chartColors.grid },
            ticks: { color: chartColors.text, maxTicksLimit: 7 },
          },
        },
      },
    });
    return charts[canvasId];
  }

  function showStatus(message, isError = false) {
    status.textContent = message;
    status.classList.toggle("is-error", isError);
  }

  function formatScore(score) {
    return score === null || score === undefined
      ? "Outside searched period range"
      : Number(score).toFixed(2);
  }

  function updateSummary(data) {
    const result = data.result;
    const aliases = result.alias_scores;
    const isControl = data.name === "control";

    document.getElementById("detected-period").textContent =
      `${result.best_period.toFixed(6)} days` +
      (isControl ? " (strongest noise peak, not a detection)" : "");

    document.getElementById("nasa-period").textContent =
      data.nasa_period === null
        ? "Not applicable to this control sample"
        : `${data.nasa_period.toFixed(6)} days`;

    document.getElementById("period-difference").textContent =
      data.percent_difference_from_nasa === null
        ? "Not applicable"
        : `${data.percent_difference_from_nasa.toFixed(4)}%`;

    document.getElementById("transit-depth").textContent = isControl
      ? "Not meaningful (no significant detection)"
      : `${(result.depth * 100).toFixed(3)}% (${(result.depth * 1e6).toFixed(0)} ppm)`;

    document.getElementById("radius-ratio").textContent = isControl
      ? "Not meaningful (no significant detection)"
      : `${Math.sqrt(Math.max(0, result.depth)).toFixed(4)} (simplified estimate)`;

    document.getElementById("significance").textContent =
      `${result.significance.toFixed(1)} (score scatter units)`;
    document.getElementById("half-alias").textContent = formatScore(aliases.half_period);
    document.getElementById("double-alias").textContent = formatScore(aliases.double_period);
  }

  function updateCharts(data) {
    scatterChart(
      "raw-chart",
      "Raw brightness",
      data.raw_light_curve.time.map((time, index) => ({
        x: time,
        y: data.raw_light_curve.flux[index],
      })),
      "Time (BKJD)",
      "Relative brightness",
      { pointRadius: 1.3, showLine: false, xMin: 100 },
    );

    scatterChart(
      "cleaned-chart",
      "Cleaned brightness",
      data.cleaned_light_curve.time.map((time, index) => ({
        x: time,
        y: data.cleaned_light_curve.flux[index],
      })),
      "Time (BKJD)",
      "Normalized flux",
      { pointRadius: 1.3, showLine: false, xMin: 100 },
    );

    const periodogramPoints = data.periodogram.period.map((period, index) => ({
      x: period,
      y: data.periodogram.score[index],
    }));
    const strongestPoint = periodogramPoints.reduce(
      (best, point) => (point.y > best.y ? point : best),
      periodogramPoints[0],
    );
    const periodChart = scatterChart(
      "periodogram-chart",
      "Period-search score",
      periodogramPoints,
      "Trial period (days)",
      "Signal score",
      { pointRadius: 0.7 },
    );
    periodChart.data.datasets.push({
      label: "Strongest peak",
      data: [strongestPoint],
      showLine: false,
      pointRadius: 5,
      pointHoverRadius: 7,
      pointBackgroundColor: chartColors.highlight,
      borderColor: chartColors.highlight,
    });
    periodChart.update("none");

    // Same fixed vertical scale for every star, so noise cannot look like a transit.
    scatterChart(
      "folded-chart",
      "Phase-folded brightness",
      data.phase_folded.phase_hours.map((phase, index) => ({
        x: phase,
        y: data.phase_folded.flux[index],
      })),
      "Hours from transit midpoint",
      "Normalized flux",
      { pointRadius: 3, yMin: 0.988, yMax: 1.002 },
    );
  }

  function updateCaptions(name, data) {
    const periodCaption = document.getElementById("period-caption");
    const foldedCaption = document.getElementById("folded-caption");

    if (name === "control") {
      periodCaption.textContent =
        "For this control star, the strongest peak is noise, not a significant detection. " +
        "The search still reports its best-fitting trial period, but it should not be " +
        "interpreted as a planet signal.";
      foldedCaption.textContent =
        "Folded on the strongest noise peak, on the same vertical scale as the planet " +
        "stars. The curve is flat: no transit-like dip is present.";
    } else {
      periodCaption.textContent =
        `${DEFAULT_PERIOD_CAPTION} The marked peak corresponds to a best-fitting period ` +
        `of ${data.result.best_period.toFixed(4)} days. The smaller spikes sit at ` +
        "multiples and fractions of this period, because a repeating dip also lines up " +
        "partly at those spacings.";
      foldedCaption.textContent = DEFAULT_FOLDED_CAPTION;
    }
  }

  async function loadStar(name) {
    showStatus(`Loading ${selector.options[selector.selectedIndex].text}…`);
    try {
      const response = await fetch(`/api/star/${encodeURIComponent(name)}`);
      if (!response.ok) {
        throw new Error(`The star data request failed (HTTP ${response.status}).`);
      }
      const data = await response.json();
      updateCharts(data);
      updateSummary(data);
      updateCaptions(name, data);
      showStatus("");
    } catch (error) {
      showStatus(
        error instanceof Error
          ? error.message
          : "Could not load this star’s precomputed data.",
        true,
      );
    }
  }

  if (typeof Chart === "undefined") {
    showStatus(
      "The chart library did not load. Check your internet connection and reload the page.",
      true,
    );
    return;
  }

  selector.addEventListener("change", () => loadStar(selector.value));
  loadStar(selector.value);
})();