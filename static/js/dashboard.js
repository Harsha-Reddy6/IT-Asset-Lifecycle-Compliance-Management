/**
 * IT Asset Platform - Dashboard Charts Integration
 * Powered by Chart.js using dynamic server-rendered MySQL aggregates
 */

document.addEventListener("DOMContentLoaded", function () {
  if (typeof Chart === "undefined") {
    console.warn("Chart.js is not loaded.");
    return;
  }

  // Chart Global Options
  Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
  Chart.defaults.font.size = 12;
  Chart.defaults.color = "#64748b";
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 6;

  // 1. Asset Status Chart (Doughnut)
  const elStatus = document.getElementById("chartAssetStatus");
  if (elStatus && window.chartAssetStatusData) {
    const rawData = window.chartAssetStatusData;
    const colors = {
      "Available": "#10b981",
      "Assigned": "#3b82f6",
      "Under Maintenance": "#f59e0b",
      "Retired": "#ef4444"
    };
    const bgColors = rawData.labels.map(l => colors[l] || "#94a3b8");

    new Chart(elStatus, {
      type: "doughnut",
      data: {
        labels: rawData.labels,
        datasets: [{
          data: rawData.data,
          backgroundColor: bgColors,
          borderWidth: 2,
          borderColor: "#ffffff"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom" }
        },
        cutout: "65%"
      }
    });
  }

  // 2. Assets by Category Chart (Bar)
  const elCat = document.getElementById("chartAssetCategories");
  if (elCat && window.chartCategoriesData) {
    const rawData = window.chartCategoriesData;
    new Chart(elCat, {
      type: "bar",
      data: {
        labels: rawData.labels,
        datasets: [{
          label: "Assets",
          data: rawData.data,
          backgroundColor: "#3b82f6",
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: { beginAtZero: true, ticks: { stepSize: 1 } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // 3. Monthly Purchases Chart (Line with area fill)
  const elPurchases = document.getElementById("chartPurchases");
  if (elPurchases && window.chartPurchasesData) {
    const rawData = window.chartPurchasesData;
    new Chart(elPurchases, {
      type: "line",
      data: {
        labels: rawData.labels,
        datasets: [{
          label: "Expenditure ($)",
          data: rawData.spend,
          borderColor: "#2563eb",
          backgroundColor: "rgba(37, 99, 235, 0.1)",
          fill: true,
          tension: 0.35,
          pointRadius: 4,
          pointBackgroundColor: "#2563eb"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                return "$" + ctx.parsed.y.toLocaleString(undefined, { minimumFractionDigits: 2 });
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: value => "$" + value.toLocaleString()
            }
          },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // 4. Software License Status Chart (Doughnut)
  const elLicenses = document.getElementById("chartLicenses");
  if (elLicenses && window.chartLicensesData) {
    const rawData = window.chartLicensesData;
    const colors = {
      "Active": "#10b981",
      "Expired": "#ef4444",
      "Cancelled": "#94a3b8"
    };
    const bgColors = rawData.labels.map(l => colors[l] || "#94a3b8");

    new Chart(elLicenses, {
      type: "doughnut",
      data: {
        labels: rawData.labels,
        datasets: [{
          data: rawData.data,
          backgroundColor: bgColors,
          borderWidth: 2,
          borderColor: "#ffffff"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom" }
        },
        cutout: "65%"
      }
    });
  }

  // 5. Compliance Alerts Chart (Bar)
  const elComp = document.getElementById("chartCompliance");
  if (elComp && window.chartComplianceData) {
    const rawData = window.chartComplianceData;
    new Chart(elComp, {
      type: "bar",
      data: {
        labels: rawData.labels,
        datasets: [{
          label: "Open Alerts",
          data: rawData.data,
          backgroundColor: "#f59e0b",
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: { beginAtZero: true, ticks: { stepSize: 1 } },
          x: { grid: { display: false } }
        }
      }
    });
  }
});
