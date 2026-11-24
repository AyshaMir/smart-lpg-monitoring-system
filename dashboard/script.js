
"use strict";

// Smart LPG Dashboard
// Demo readings and live Pico API support.

const $ = (id) => document.getElementById(id);

// Simulated readings for home testing.
const demoSamples = {
    normal: {
        gas_kg: 2.4,
        gas_percent: 80,
        mq5_voltage: 1.2,
        gas_status: "BASELINE",
        leak: false,
        alert_state: "NORMAL",
        days_left: null
    },

    low: {
        gas_kg: 0.6,
        gas_percent: 20,
        mq5_voltage: 1.2,
        gas_status: "BASELINE",
        leak: false,
        alert_state: "LOW_GAS",
        days_left: null
    },

    leak: {
        gas_kg: 2.4,
        gas_percent: 80,
        mq5_voltage: 2.7,
        gas_status: "HIGH_RESPONSE",
        leak: true,
        alert_state: "LEAK_DETECTED",
        days_left: null
    },

    fault: {
        gas_kg: null,
        gas_percent: null,
        mq5_voltage: null,
        gas_status: "UNAVAILABLE",
        leak: null,
        alert_state: "FAULT",
        days_left: null
    }
};

let source = "demo";
let demoChoice = "normal";
let inflight = false;
let requestController = null;

const finiteNumber = (n) =>
    typeof n === "number" && Number.isFinite(n);

function valueOrDash(n, digits, unit) {
    return finiteNumber(n)
        ? n.toFixed(digits) + unit
        : "--" + unit;
}

function showStatus(label, kind) {
    const node = $("connection-status");

    node.textContent = label;
    node.className = "status-pill" +
        (kind ? " " + kind : "");
}


// =====================================
// SENSOR HISTORY STORAGE
// =====================================

const HISTORY_LIMIT = 300;
const HISTORY_KEY_PREFIX = "smartLpgHistoryV1_";

const historyStore = {
    demo: [],
    live: []
};


// Load previously saved history.
function loadHistory(kind) {
    try {
        const raw = JSON.parse(
            localStorage.getItem(
                HISTORY_KEY_PREFIX + kind
            ) || "[]"
        );

        if (!Array.isArray(raw)) {
            return [];
        }

        return raw
            .filter(row =>
                row && finiteNumber(row.t)
            )
            .slice(-HISTORY_LIMIT);

    } catch (error) {
        return [];
    }
}


// Save history in browser storage.
function saveHistory(kind) {
    try {
        localStorage.setItem(
            HISTORY_KEY_PREFIX + kind,
            JSON.stringify(historyStore[kind])
        );

    } catch (error) {
        $("history-info").textContent =
            "Browser storage unavailable.";
    }
}


// Record one sensor sample.
function addHistorySample(data, kind) {
    const row = {
        t: Date.now(),

        gas_kg: finiteNumber(data.gas_kg)
            ? data.gas_kg
            : null,

        mq5_voltage: finiteNumber(data.mq5_voltage)
            ? data.mq5_voltage
            : null
    };

    // Do not record completely empty readings.
    if (
        row.gas_kg === null &&
        row.mq5_voltage === null
    ) {
        return;
    }

    historyStore[kind].push(row);

    // Keep only the newest 300 samples.
    historyStore[kind] =
        historyStore[kind].slice(-HISTORY_LIMIT);

    saveHistory(kind);

    if (source === kind) {
        drawHistory();
    }
}


// =====================================
// HISTORY GRAPH
// =====================================

function drawHistory() {
    const canvas = $("history-chart");
    const container = canvas.parentElement;

    const width = Math.max(
        300,
        container.clientWidth
    );

    const height = 270;

    const dpr = Math.min(
        window.devicePixelRatio || 1,
        2
    );

    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);

    const ctx = canvas.getContext("2d");

    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    const key = $("history-metric").value;

    const all = historyStore[source];

    const samples = all.filter(
        row => finiteNumber(row[key])
    );

    $("sample-btn").disabled = source !== "demo";

    $("history-info").textContent =
        `${all.length} saved ${source} samples. ` +
        (source === "demo"
            ? "Simulated data."
            : "Live browser-recorded data.");

    ctx.font = "12px Arial";
    ctx.fillStyle = "#64748b";

    if (samples.length === 0) {
        ctx.fillText(
            "No valid readings recorded yet.",
            24,
            135
        );
        return;
    }

    const left = 58;
    const right = 18;
    const top = 23;
    const bottom = 45;

    const plotWidth = width - left - right;
    const plotHeight = height - top - bottom;

    const values = samples.map(
        row => row[key]
    );

    let min = Math.min(...values);
    let max = Math.max(...values);

    const padding = Math.max(
        (max - min) * 0.15,
        key === "gas_kg" ? 0.1 : 0.05
    );

    min = Math.max(0, min - padding);
    max += padding;

    if (max === min) {
        max = min + 1;
    }

    const times = samples.map(row => row.t);

    const firstTime = Math.min(...times);
    const lastTime = Math.max(...times);

    function pointX(t, index) {
        if (lastTime === firstTime) {
            const fraction = samples.length === 1
                ? 0.5
                : index / (samples.length - 1);

            return left + fraction * plotWidth;
        }

        return left +
            ((t - firstTime) /
             (lastTime - firstTime)) * plotWidth;
    }

    function pointY(value) {
        return top +
            ((max - value) / (max - min))
            * plotHeight;
    }

    // Horizontal grid lines.
    ctx.strokeStyle = "#e4ece7";
    ctx.lineWidth = 1;

    for (let i = 0; i <= 4; i++) {
        const y = top + i * plotHeight / 4;

        ctx.beginPath();
        ctx.moveTo(left, y);
        ctx.lineTo(width - right, y);
        ctx.stroke();

        const tick =
            max - i * (max - min) / 4;

        ctx.fillStyle = "#64748b";
        ctx.fillText(tick.toFixed(2), 8, y + 4);
    }

    // Graph line.
    ctx.strokeStyle =
        key === "gas_kg" ? "#15803d" : "#2563eb";

    ctx.lineWidth = 2;
    ctx.beginPath();

    samples.forEach((row, index) => {
        const x = pointX(row.t, index);
        const y = pointY(row[key]);

        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });

    ctx.stroke();

    // Data points.
    samples.forEach((row, index) => {
        const x = pointX(row.t, index);
        const y = pointY(row[key]);

        ctx.beginPath();
        ctx.arc(x, y, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = ctx.strokeStyle;
        ctx.fill();
    });

    // Time labels.
    ctx.fillStyle = "#64748b";
    ctx.textAlign = "left";

    ctx.fillText(
        new Date(firstTime).toLocaleTimeString(),
        left,
        height - 17
    );

    ctx.textAlign = "right";

    ctx.fillText(
        new Date(lastTime).toLocaleTimeString(),
        width - right,
        height - 17
    );

    ctx.textAlign = "left";
}


// =====================================
// EXPORT HISTORY AS CSV
// =====================================

function exportHistory() {
    const rows = historyStore[source];

    if (!rows.length) {
        alert("No history to export yet.");
        return;
    }

    const lines = [
        "timestamp,gas_kg,mq5_voltage"
    ];

    rows.forEach(row => {
        lines.push([
            new Date(row.t).toISOString(),
            row.gas_kg ?? "",
            row.mq5_voltage ?? ""
        ].join(","));
    });

    const blob = new Blob(
        [lines.join("\n")],
        { type: "text/csv;charset=utf-8" }
    );

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download =
        `smart-lpg-${source}-history.csv`;

    link.click();

    setTimeout(() => {
        URL.revokeObjectURL(url);
    }, 1000);
}


// =====================================
// DASHBOARD DISPLAY
// =====================================

function render(data) {
    const percent = finiteNumber(data.gas_percent)
        ? Math.max(0, Math.min(100, data.gas_percent))
        : null;

    $("gas-kg").textContent =
        valueOrDash(data.gas_kg, 2, " kg");

    $("cylinder-percent").textContent =
        percent === null
            ? "--%"
            : Math.round(percent) + "%";

    $("cylinder-fill").style.height =
        (percent === null ? 0 : percent) + "%";

    $("days-left").textContent =
        finiteNumber(data.days_left)
            ? Math.round(
                Math.max(0, data.days_left)
              ) + " days"
            : "--";

    $("mq5-reading").textContent =
        valueOrDash(data.mq5_voltage, 2, " V");

    $("mq5-status").textContent =
        "Status: " +
        (
            typeof data.gas_status === "string"
                ? data.gas_status.replaceAll("_", " ")
                : "unavailable"
        );

    // Use the firmware's alert decision.
    let state = data.alert_state;

    if (![
        "NORMAL",
        "LOW_GAS",
        "LEAK_DETECTED",
        "FAULT"
    ].includes(state)) {
        state = data.leak === true
            ? "LEAK_DETECTED"
            : "FAULT";
    }

    const messages = {
        NORMAL:
            "Normal monitoring status — LPG above 20% and no suspected leak.",

        LOW_GAS:
            "Low LPG — 20% remaining or below.",

        LEAK_DETECTED:
            "Suspected gas response — red alert. Prototype readings are not certified.",

        FAULT:
            "Status unavailable — sensor disconnected or not reporting."
    };

    const banner = $("alert-banner");

    banner.className = "alert-banner";

    if (state === "LOW_GAS") {
        banner.classList.add("alert-low");
    } else if (state === "LEAK_DETECTED") {
        banner.classList.add("alert-leak");
    } else if (state === "FAULT") {
        banner.classList.add("alert-fault");
    }

    $("alert-text").textContent = messages[state];
}


// =====================================
// LIVE PICO API
// =====================================

async function refreshLive() {
    if (source !== "live" || inflight) {
        return;
    }

    const url = $("api-url").value.trim();

    if (!/^https?:\/\//i.test(url)) {
        showStatus("Invalid API URL", "error");
        return;
    }

    inflight = true;

    const controller = new AbortController();
    requestController = controller;

    const timeoutId = setTimeout(
        () => controller.abort(),
        1800
    );

    try {
        const response = await fetch(url, {
            cache: "no-store",
            signal: controller.signal
        });

        if (!response.ok) {
            throw new Error(
                "HTTP " + response.status
            );
        }

        const data = await response.json();

        if (
            !data ||
            typeof data !== "object" ||
            !("gas_status" in data)
        ) {
            throw new Error(
                "Unexpected API response"
            );
        }

        if (
            source !== "live" ||
            requestController !== controller
        ) {
            return;
        }

        render(data);
        addHistorySample(data, "live");

        showStatus(
            "LIVE — Pico connected",
            "live"
        );

        $("last-update").textContent =
            "Last live update: " +
            new Date().toLocaleTimeString();

    } catch (error) {
        if (
            source === "live" &&
            requestController === controller
        ) {
            render(demoSamples.fault);

            showStatus(
                "DISCONNECTED — no live readings",
                "error"
            );

            $("last-update").textContent =
                "Unable to read Pico API: " +
                String(error.message || error);
        }

    } finally {
        clearTimeout(timeoutId);

        if (requestController === controller) {
            requestController = null;
        }

        inflight = false;
    }
}


// =====================================
// DEMO / LIVE SOURCE SWITCHING
// =====================================

function setSource(next) {
    source = next;

    if (requestController) {
        requestController.abort();
    }

    $("api-url").disabled = next !== "live";

    $("demo-controls").hidden =
        next !== "demo";

    if (next === "demo") {
        render(demoSamples[demoChoice]);

        drawHistory();

        showStatus(
            "DEMO — simulated data",
            ""
        );

        $("last-update").textContent =
            "Simulated readings only.";

    } else {
        render(demoSamples.fault);

        drawHistory();

        showStatus(
            "CONNECTING — waiting for Pico",
            ""
        );

        $("last-update").textContent =
            "Attempting to fetch live readings...";

        refreshLive();
    }
}


// =====================================
// BUTTON EVENT LISTENERS
// =====================================

document.querySelectorAll(
    'input[name="source"]'
).forEach(node => {
    node.addEventListener("change", () => {
        if (node.checked) {
            setSource(node.value);
        }
    });
});

document.querySelectorAll(
    "[data-demo]"
).forEach(button => {
    button.addEventListener("click", () => {
        demoChoice = button.dataset.demo;

        if (source === "demo") {
            const data = demoSamples[demoChoice];

            render(data);
            addHistorySample(data, "demo");
        }
    });
});

$("refresh-btn").addEventListener(
    "click",
    () => {
        if (source === "live") {
            refreshLive();
        } else {
            render(demoSamples[demoChoice]);
        }
    }
);

$("history-metric").addEventListener(
    "change",
    drawHistory
);

$("sample-btn").addEventListener(
    "click",
    () => {
        if (source === "demo") {
            addHistorySample(
                demoSamples[demoChoice],
                "demo"
            );
        }
    }
);

$("csv-btn").addEventListener(
    "click",
    exportHistory
);

$("clear-history-btn").addEventListener(
    "click",
    () => {
        const confirmed = confirm(
            `Clear all ${source} history?`
        );

        if (!confirmed) {
            return;
        }

        historyStore[source] = [];

        saveHistory(source);
        drawHistory();
    }
);

window.addEventListener(
    "resize",
    drawHistory
);


// =====================================
// INITIALIZATION
// =====================================

for (const kind of ["demo", "live"]) {
    historyStore[kind] = loadHistory(kind);
}

// Live refresh every 2 seconds.
setInterval(() => {
    if (source === "live") {
        refreshLive();
    }
}, 2000);

setSource("demo");
