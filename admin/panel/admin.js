/**
 * Admin Panel JavaScript
 * Button-based control interface for Property Monitor IF
 * Manages all 5 modules through REST API calls
 */

// API Configuration - PRODUCTION ONLY
const API_BASE_URL = "https://glow-nest-api.fly.dev";

// Global state
let eventSource = null;
let mlProgressSource = null;
let refreshInterval = null;

// Initialize when page loads
document.addEventListener("DOMContentLoaded", function () {
  console.log("🚀 Initializing Property Monitor Admin Panel");

  // Start real-time updates
  initializeRealTimeUpdates();

  // Load initial system status
  loadSystemStatus();

  // Start periodic updates
  startPeriodicUpdates();
});

// Real-time updates using Server-Sent Events
function initializeRealTimeUpdates() {
  // Event log stream
  if (eventSource) {
    eventSource.close();
  }

  eventSource = new EventSource(`${API_BASE_URL}/events/stream`);

  eventSource.onmessage = function (event) {
    try {
      const eventData = JSON.parse(event.data);
      addLogEntry(eventData);
    } catch (e) {
      console.error("Error parsing event data:", e);
    }
  };

  eventSource.onerror = function (error) {
    console.error("EventSource error:", error);
    addLogEntry({
      module: "system",
      action: "connection_error",
      details: "Втрачено зв'язок з сервером",
      status: "ERROR",
    });
  };
}

// Load system status
async function loadSystemStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/system/status`);
    const status = await response.json();

    updateSystemOverview(status);
    updateModuleStatuses(status);
  } catch (error) {
    console.error("Error loading system status:", error);
    showAlert("Помилка завантаження статусу системи", "error");
  }
}

// Update system overview metrics
function updateSystemOverview(status) {
  // Get property statistics
  fetch(`${API_BASE_URL}/properties/stats`)
    .then((response) => response.json())
    .then((stats) => {
      document.getElementById("totalProperties").textContent =
        stats.total_properties || 0;
    })
    .catch(console.error);

  // Count active modules
  const activeModules = Object.values(status).filter(
    (module) => module && module.status === "running",
  ).length;

  document.getElementById("activeModules").textContent = activeModules;
  document.getElementById("lastUpdate").textContent =
    new Date().toLocaleTimeString("uk-UA");
  document.getElementById("systemStatus").textContent = "✅ Онлайн";
}

// Update individual module statuses
function updateModuleStatuses(status) {
  // Scraper status
  const scraperStatus = status.scraper || {};
  updateModuleStatus(
    "scraper",
    scraperStatus.status || "idle",
    scraperStatus.progress || 0,
  );

  // ML status
  const mlStatus = status.ml || {};
  updateModuleStatus("ml", mlStatus.status || "idle", mlStatus.progress || 0);

  // Prophet status
  const prophetStatus = status.prophet || {};
  updateModuleStatus(
    "prophet",
    prophetStatus.status || "idle",
    prophetStatus.progress || 0,
  );

  // Streamlit status
  const streamlitStatus = status.streamlit || {};
  updateModuleStatus("streamlit", streamlitStatus.status || "stopped", 0);

  // Superset status (always available)
  updateModuleStatus("superset", "available", 0);
}

// Update module status display
function updateModuleStatus(module, status, progress) {
  const statusElement = document.getElementById(`${module}Status`);
  const progressElement = document.getElementById(`${module}Progress`);

  // Update status text and class
  if (statusElement) {
    statusElement.textContent = getStatusText(status);
    statusElement.className = `module-status status-${status}`;
  }

  // Update progress bar
  if (progressElement) {
    progressElement.style.width = `${progress}%`;
  }
}

// Get status text in Ukrainian
function getStatusText(status) {
  const statusMap = {
    idle: "Неактивний",
    running: "Запущено",
    training: "Навчання",
    completed: "Завершено",
    error: "Помилка",
    failed: "Невдача",
    stopped: "Зупинено",
    available: "Доступно",
  };

  return statusMap[status] || status;
}

// Add log entry to live log viewer
function addLogEntry(eventData) {
  const logViewer = document.getElementById("eventLog");
  const timestamp = new Date().toLocaleTimeString("uk-UA");

  const logClass = `log-${eventData.status?.toLowerCase() || "info"}`;
  const logEntry = document.createElement("div");
  logEntry.className = `log-entry ${logClass}`;
  logEntry.textContent = `[${timestamp}] [${eventData.module?.toUpperCase()}] ${eventData.details}`;

  // Add to top of log
  logViewer.insertBefore(logEntry, logViewer.firstChild);

  // Keep only last 50 entries
  while (logViewer.children.length > 50) {
    logViewer.removeChild(logViewer.lastChild);
  }
}

// Periodic updates
function startPeriodicUpdates() {
  refreshInterval = setInterval(() => {
    loadSystemStatus();
  }, 5000); // Update every 5 seconds
}

// Backend deployment
async function deployBackend() {
  try {
    showButtonLoading("deployBackendBtn");
    const response = await fetch(`${API_BASE_URL}/deploy`, { method: "POST" });
    const result = await response.json();

    if (result.success) {
      showAlert("✅ Backend deployment started", "success");
    } else {
      showAlert(`❌ ${result.message || "Deployment failed"}`, "error");
    }
  } catch (error) {
    console.error("Error deploying backend:", error);
    showAlert("❌ Deployment request failed", "error");
  } finally {
    hideButtonLoading();
  }
}

// Module 1: Scraper functions
async function startScraping(listingType) {
  try {
    showButtonLoading("startScraping");

    const response = await fetch(`${API_BASE_URL}/scraper/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        listing_type: listingType,
        max_pages: 10,
        delay_ms: 5000,
      }),
    });

    const result = await response.json();

    if (result.success) {
      showAlert(
        `✅ Скрапінг ${listingType} запущено! ${result.message}`,
        "success",
      );
      updateModuleStatus("scraper", "running", 0);
    } else {
      showAlert(`❌ Помилка: ${result.error || "Невідома помилка"}`, "error");
    }
  } catch (error) {
    console.error("Error starting scraping:", error);
    showAlert("❌ Помилка запуску скрапінгу", "error");
  } finally {
    hideButtonLoading();
  }
}

async function stopScraping() {
  try {
    const response = await fetch(`${API_BASE_URL}/scraper/stop`, {
      method: "POST",
    });

    const result = await response.json();

    if (result.success) {
      showAlert("⏹️ Скрапінг зупинено", "warning");
      updateModuleStatus("scraper", "idle", 0);
    } else {
      showAlert(`❌ ${result.message}`, "warning");
    }
  } catch (error) {
    console.error("Error stopping scraping:", error);
    showAlert("❌ Помилка зупинки скрапінгу", "error");
  }
}

async function getScrapingStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/scraper/status`);
    const status = await response.json();

    const message = `
            Статус: ${getStatusText(status.status)}
            Прогрес: ${status.progress || 0}%
            ${status.result ? `Результат: ${JSON.stringify(status.result)}` : ""}
        `;

    showAlert(message, "info");
  } catch (error) {
    console.error("Error getting scraper status:", error);
    showAlert("❌ Помилка отримання статусу", "error");
  }
}

// Module 2: ML functions
async function trainMLModel() {
  try {
    showButtonLoading("trainML");

    const response = await fetch(`${API_BASE_URL}/ml/train`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_mape: 15.0,
        timeout: 3600,
      }),
    });

    const result = await response.json();

    if (result.success) {
      showAlert(
        `🏋️ Навчання моделі запущено! Ціль: MAPE ≤ ${result.target_mape}%`,
        "success",
      );
      updateModuleStatus("ml", "training", 0);

      // Start ML progress monitoring
      startMLProgressMonitoring();
    } else {
      showAlert(`❌ Помилка: ${result.error}`, "error");
    }
  } catch (error) {
    console.error("Error training ML model:", error);
    showAlert("❌ Помилка запуску навчання", "error");
  } finally {
    hideButtonLoading();
  }
}

function startMLProgressMonitoring() {
  if (mlProgressSource) {
    mlProgressSource.close();
  }

  mlProgressSource = new EventSource(`${API_BASE_URL}/ml/progress/stream`);

  mlProgressSource.onmessage = function (event) {
    try {
      const progress = JSON.parse(event.data);

      updateModuleStatus("ml", progress.status, progress.progress);

      if (progress.status === "completed") {
        showAlert(
          `✅ Навчання завершено! MAPE: ${progress.final_mape}%`,
          "success",
        );
        mlProgressSource.close();
      } else if (progress.status === "failed") {
        showAlert(`❌ Навчання невдале: ${progress.error}`, "error");
        mlProgressSource.close();
      }
    } catch (e) {
      console.error("Error parsing ML progress:", e);
    }
  };
}

async function testMLPrediction() {
  try {
    const response = await fetch(`${API_BASE_URL}/ml/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        area: 65,
        district: "Цен��р",
        rooms: 2,
        floor: 5,
        total_floors: 9,
        building_type: "квартира",
        renovation_status: "хороший",
        seller_type: "owner",
      }),
    });

    const result = await response.json();

    if (result.success) {
      showAlert(
        `🔮 Тестовий прогноз: $${result.predicted_price} (65м², Центр, 2 кімнати)`,
        "info",
      );
    } else {
      showAlert(`❌ Помилка прогнозу: ${result.error}`, "error");
    }
  } catch (error) {
    console.error("Error testing ML prediction:", error);
    showAlert("❌ Помилка тестового прогнозу", "error");
  }
}

async function getMLStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/ml/status`);
    const status = await response.json();

    const metrics = status.metrics || {};
    const message = `
            Модель: ${status.model_exists ? "✅ Навчена" : "❌ Не навчена"}
            MAPE: ${metrics.mape || "н/д"}%
            R²: ${metrics.r2 || "н/д"}
            Статус: ${getStatusText(status.status)}
        `;

    showAlert(message, "info");
  } catch (error) {
    console.error("Error getting ML status:", error);
    showAlert("❌ Помилка отримання статусу ML", "error");
  }
}

// Module 3: Prophet functions
async function generateForecasts() {
  try {
    showButtonLoading("generateForecasts");

    const response = await fetch(`${API_BASE_URL}/prophet/forecast`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        forecast_months: 6,
      }),
    });

    const result = await response.json();

    if (result.success) {
      showAlert(
        `📈 Прогнозування запущено на ${result.forecast_months} місяців`,
        "success",
      );
      updateModuleStatus("prophet", "running", 0);
    } else {
      showAlert(`❌ Помилка: ${result.error}`, "error");
    }
  } catch (error) {
    console.error("Error generating forecasts:", error);
    showAlert("❌ Помилка ��енерації прогнозів", "error");
  } finally {
    hideButtonLoading();
  }
}

async function viewForecasts() {
  try {
    const response = await fetch(`${API_BASE_URL}/prophet/forecasts`);
    const forecasts = await response.json();

    if (Object.keys(forecasts).length > 0) {
      const summary = Object.keys(forecasts)
        .filter((k) => !k.startsWith("_"))
        .slice(0, 3)
        .join(", ");

      showAlert(`📊 Прогнози готові для: ${summary}...`, "info");
    } else {
      showAlert("📭 Прогнози ще не готові", "warning");
    }
  } catch (error) {
    console.error("Error viewing forecasts:", error);
    showAlert("❌ Помилка перегляду прогнозів", "error");
  }
}

async function getProphetStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/prophet/status`);
    const status = await response.json();

    const message = `
            Статус: ${getStatusText(status.status)}
            Прогрес: ${status.progress || 0}%
        `;

    showAlert(message, "info");
  } catch (error) {
    console.error("Error getting Prophet status:", error);
    showAlert("❌ Помилка отримання статусу Prophet", "error");
  }
}

// Module 4: Streamlit functions
async function controlStreamlit(action) {
  try {
    showButtonLoading("streamlitControl");

    const response = await fetch(`${API_BASE_URL}/streamlit/control`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: action,
        port: 8501,
      }),
    });

    const result = await response.json();

    if (result.success) {
      if (action === "start") {
        showAlert("🚀 Streamlit запущено на http://localhost:8501", "success");
        updateModuleStatus("streamlit", "running", 0);
      } else {
        showAlert("⏹️ Streamlit зупинено", "warning");
        updateModuleStatus("streamlit", "stopped", 0);
      }
    } else {
      showAlert(`❌ ${result.message}`, "error");
    }
  } catch (error) {
    console.error("Error controlling Streamlit:", error);
    showAlert("❌ Помилка керування Streamlit", "error");
  } finally {
    hideButtonLoading();
  }
}

// Module 5: Superset functions
async function getSupersetStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/superset/status`);
    const status = await response.json();

    const message = `
            Статус: ${status.status}
            URL: ${status.url}
            Дашборди: ${status.dashboards?.length || 0}
        `;

    showAlert(message, "info");
  } catch (error) {
    console.error("Error getting Superset status:", error);
    showAlert("❌ Помилка отримання статусу Superset", "error");
  }
}

function showSupersetInfo() {
  const info = `
        📊 Apache Superset - Інструкції по запуску:
        
        1. Встановіть Superset: pip install apache-superset
        2. Ініціалізуйте БД: superset db upgrade
        3. Створіть адміна: superset fab create-admin
        4. Запустіть сервер: superset run -p 8088 --with-threads --reload --debugger
        5. Відкрийте: http://localhost:8088
    `;

  showAlert(info, "info");
}

// Street management functions
function showStreetManager() {
  const street = prompt("Введіть назву вулиці:");
  const district = prompt("Введіть назву району:");

  if (street && district) {
    addStreetMapping(street, district);
  }
}

async function addStreetMapping(street, district) {
  try {
    const response = await fetch(`${API_BASE_URL}/streets/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ street, district }),
    });

    const result = await response.json();

    if (result.success) {
      showAlert(`✅ Додано: ${street} → ${district}`, "success");
    } else {
      showAlert(`❌ ${result.message}`, "error");
    }
  } catch (error) {
    console.error("Error adding street mapping:", error);
    showAlert("❌ Помилка додавання вулиці", "error");
  }
}

async function viewStreetMappings() {
  try {
    const response = await fetch(`${API_BASE_URL}/streets/mapping`);
    const result = await response.json();

    const mappings = result.street_mappings || {};
    const count = Object.keys(mappings).length;

    if (count > 0) {
      const sample = Object.entries(mappings)
        .slice(0, 3)
        .map(([street, district]) => `${street} → ${district}`)
        .join("\n");

      showAlert(`📍 Всього вулиць: ${count}\n\nПриклади:\n${sample}`, "info");
    } else {
      showAlert("📭 Немає збережених вулиць", "warning");
    }
  } catch (error) {
    console.error("Error viewing street mappings:", error);
    showAlert("❌ Помилка перегляду вулиць", "error");
  }
}

// UI Helper functions
function showAlert(message, type) {
  // Remove existing alerts
  const existingAlerts = document.querySelectorAll(".alert");
  existingAlerts.forEach((alert) => alert.remove());

  // Create new alert
  const alert = document.createElement("div");
  alert.className = `alert alert-${type}`;
  alert.textContent = message;

  // Insert at top of content
  const content = document.querySelector(".content");
  content.insertBefore(alert, content.firstChild);

  // Auto-remove after 5 seconds
  setTimeout(() => {
    if (alert.parentNode) {
      alert.remove();
    }
  }, 5000);
}

function showButtonLoading(buttonId) {
  // Add loading state to buttons (simplified)
  const buttons = document.querySelectorAll(".btn");
  buttons.forEach((btn) => (btn.disabled = true));
}

function hideButtonLoading() {
  // Remove loading state from buttons
  const buttons = document.querySelectorAll(".btn");
  buttons.forEach((btn) => (btn.disabled = false));
}

// Cleanup on page unload
window.addEventListener("beforeunload", function () {
  if (eventSource) {
    eventSource.close();
  }
  if (mlProgressSource) {
    mlProgressSource.close();
  }
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});

// Error handling
window.addEventListener("error", function (event) {
  console.error("Global error:", event.error);
  addLogEntry({
    module: "client",
    action: "javascript_error",
    details: `Помилка JavaScript: ${event.error?.message}`,
    status: "ERROR",
  });
});
