/**
 * SocialPlus.ai — Chart.js Visualizations Controller
 * Premium Dark Glassmorphic Theme
 */

// Set dark theme defaults for Chart.js
if (typeof Chart !== "undefined") {
  Chart.defaults.color = "#94a3b8";
  Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
  Chart.defaults.font.size = 12;
}

const ChartManager = {
  instances: {},

  destroyChart(id) {
    if (this.instances[id]) {
      this.instances[id].destroy();
      delete this.instances[id];
    }
  },

  // 1. Sentiment Donut Chart
  renderSentimentDonut(canvasId, sentimentDist) {
    this.destroyChart(canvasId);
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const labels = ["Positive", "Negative", "Neutral", "Mixed", "Sarcastic"];
    const dataValues = [
      sentimentDist.Positive || 0,
      sentimentDist.Negative || 0,
      sentimentDist.Neutral || 0,
      sentimentDist.Mixed || 0,
      sentimentDist.Sarcastic || 0,
    ];

    const colors = ["#10b981", "#f43f5e", "#94a3b8", "#f59e0b", "#a855f7"];

    this.instances[canvasId] = new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [{
          data: dataValues,
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: "rgba(18, 23, 35, 0.9)"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { boxWidth: 12, color: "#94a3b8", font: { size: 12, weight: 600 } }
          },
          tooltip: {
            backgroundColor: "rgba(13, 17, 27, 0.95)",
            titleColor: "#f8fafc",
            bodyColor: "#f8fafc",
            borderColor: "rgba(255, 255, 255, 0.12)",
            borderWidth: 1,
            callbacks: {
              label: (item) => ` ${item.label}: ${item.raw}%`
            }
          }
        },
        cutout: "65%"
      }
    });
  },

  // 2. Emotion Intelligence Horizontal Bar
  renderEmotionsBar(canvasId, emotionDist) {
    this.destroyChart(canvasId);
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const labels = Object.keys(emotionDist);
    const percentages = labels.map(k => emotionDist[k].percentage);

    this.instances[canvasId] = new Chart(canvas, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "Emotion Presence (%)",
          data: percentages,
          backgroundColor: "rgba(56, 189, 248, 0.85)",
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: "y",
        scales: {
          x: {
            beginAtZero: true,
            max: 100,
            grid: { color: "rgba(255, 255, 255, 0.05)" },
            ticks: { color: "#94a3b8", callback: (v) => `${v}%` }
          },
          y: {
            grid: { display: false },
            ticks: { color: "#f8fafc", font: { weight: 500 } }
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "rgba(13, 17, 27, 0.95)",
            titleColor: "#f8fafc",
            bodyColor: "#f8fafc",
            borderColor: "rgba(255, 255, 255, 0.12)",
            borderWidth: 1
          }
        }
      }
    });
  },

  // 3. Comment Intent Horizontal Bar
  renderIntentBar(canvasId, intentDist) {
    this.destroyChart(canvasId);
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const labels = Object.keys(intentDist);
    const counts = labels.map(k => intentDist[k].count);

    this.instances[canvasId] = new Chart(canvas, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "Comment Count",
          data: counts,
          backgroundColor: "rgba(245, 158, 11, 0.85)",
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: "y",
        scales: {
          x: {
            beginAtZero: true,
            grid: { color: "rgba(255, 255, 255, 0.05)" },
            ticks: { color: "#94a3b8" }
          },
          y: {
            grid: { display: false },
            ticks: { color: "#f8fafc", font: { weight: 500 } }
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "rgba(13, 17, 27, 0.95)",
            titleColor: "#f8fafc",
            bodyColor: "#f8fafc",
            borderColor: "rgba(255, 255, 255, 0.12)",
            borderWidth: 1
          }
        }
      }
    });
  },

  // 4. Auto-Moderation Doughnut Chart
  renderModerationChart(canvasId, modDist) {
    this.destroyChart(canvasId);
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const labels = ["Safe", "Review Required", "Suspicious", "Spam", "Toxic"];
    const counts = labels.map(k => modDist[k] || 0);
    const bgColors = ["#10b981", "#f59e0b", "#f97316", "#f43f5e", "#a855f7"];

    this.instances[canvasId] = new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [{
          data: counts,
          backgroundColor: bgColors,
          borderWidth: 2,
          borderColor: "rgba(18, 23, 35, 0.9)"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { boxWidth: 12, color: "#94a3b8", font: { size: 12, weight: 600 } }
          },
          tooltip: {
            backgroundColor: "rgba(13, 17, 27, 0.95)",
            titleColor: "#f8fafc",
            bodyColor: "#f8fafc",
            borderColor: "rgba(255, 255, 255, 0.12)",
            borderWidth: 1
          }
        },
        cutout: "60%"
      }
    });
  }
};
