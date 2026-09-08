// Chart.js Helper Utilities for OnionGrade AI

function createQualityDonutChart(canvasId, healthy, damaged, rotten, sprouted) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  return new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Healthy", "Damaged", "Rotten", "Sprouted"],
      datasets: [{
        data: [healthy, damaged, rotten, sprouted],
        backgroundColor: [
          "#16a34a", // Healthy - Green
          "#d97706", // Damaged - Amber
          "#dc2626", // Rotten - Crimson Red
          "#ea580c"  // Sprouted - Orange
        ],
        borderWidth: 2,
        borderColor: "#ffffff",
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            font: { family: "'Inter', sans-serif", size: 12, weight: 600 },
            padding: 14,
            usePointStyle: true
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const val = context.raw || 0;
              const pct = total ? ((val / total) * 100).toFixed(1) : 0;
              return ` ${context.label}: ${val} (${pct}%)`;
            }
          }
        }
      },
      cutout: "68%"
    }
  });
}

function createGradeBarChart(canvasId, gradeA, urs, rejected) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  return new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Grade A (Healthy)", "URS (Damaged)", "Rejected (Rotten+Sprouted)"],
      datasets: [{
        label: "Onions",
        data: [gradeA, urs, rejected],
        backgroundColor: [
          "rgba(22, 163, 74, 0.85)",
          "rgba(217, 119, 6, 0.85)",
          "rgba(220, 38, 38, 0.85)"
        ],
        borderColor: ["#16a34a", "#d97706", "#dc2626"],
        borderWidth: 1.5,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: "#f1f5f9" },
          ticks: { precision: 0, font: { family: "'Inter', sans-serif" } }
        },
        x: {
          grid: { display: false },
          ticks: { font: { family: "'Inter', sans-serif", weight: 600 } }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

function createPriceTrendChart(canvasId, trendData) {
  const ctx = document.getElementById(canvasId);
  if (!ctx || !trendData) return null;

  const labels = trendData.map(d => d.date);
  const lasalgaon = trendData.map(d => d.lasalgaon);
  const pune = trendData.map(d => d.pune);
  const delhi = trendData.map(d => d.delhi);

  return new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Lasalgaon Mandi (Nashik)",
          data: lasalgaon,
          borderColor: "#0f5132",
          backgroundColor: "rgba(15, 81, 50, 0.08)",
          fill: true,
          tension: 0.3,
          borderWidth: 2.5
        },
        {
          label: "Pune APMC",
          data: pune,
          borderColor: "#2563eb",
          tension: 0.3,
          borderWidth: 2,
          borderDash: [5, 5]
        },
        {
          label: "Azadpur Mandi (Delhi)",
          data: delhi,
          borderColor: "#d97706",
          tension: 0.3,
          borderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          ticks: {
            callback: value => "₹" + value,
            font: { family: "'Inter', sans-serif" }
          },
          grid: { color: "#f1f5f9" }
        },
        x: {
          grid: { display: false },
          ticks: { font: { family: "'Inter', sans-serif" } }
        }
      },
      plugins: {
        legend: {
          position: "top",
          labels: { usePointStyle: true, font: { weight: 600 } }
        }
      }
    }
  });
}
