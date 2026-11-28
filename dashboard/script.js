
"use strict";

// SMART LPG MONITORING DASHBOARD

const $ = id => document.getElementById(id);
const LPG_CAPACITY_KG = 3.0;
const finiteNumber = n => typeof n === "number" && Number.isFinite(n);

function valueOrDash(n, digits, unit) {
    return finiteNumber(n) ? n.toFixed(digits) + unit : "--" + unit;
}

function formatPKR(value) {
    return Number.isFinite(value) ? "Rs. " + value.toFixed(2) : "Rs. --";
}

function showStatus(label, kind = "") {
    const node = $("connection-status");
    node.textContent = label;
    node.className = "status-pill" + (kind ? " " + kind : "");
}

// DEMO DATA

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
        gas_status: "POSSIBLE_GAS",
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
let demoCurrentData = { ...demoSamples.normal };
let currentCostData = { ...demoSamples.normal };
let inflight = false;
let requestController = null;

// CONSUMPTION PREDICTIONS

let demoPrediction = null;

function calculateConsumption(readings) {
    const valid = readings.filter(row =>
        row && Number.isFinite(row.t) &&
        Number.isFinite(row.gas_kg) && row.gas_kg >= 0
    ).sort((a, b) => a.t - b.t);

    if (valid.length < 2) return null;

    const first = valid[0];
    const last = valid[valid.length - 1];
    const elapsedDays = (last.t - first.t) / 86400000;

    if (elapsedDays < 1) return null;

    for (let i = 1; i < valid.length; i++) {
        if (valid[i].gas_kg > valid[i - 1].gas_kg) return null;
    }

    const consumed = first.gas_kg - last.gas_kg;
    if (consumed <= 0) return null;

    const dailyRate = consumed / elapsedDays;

    return {
        dailyRate,
        days: last.gas_kg / dailyRate
    };
}

function simulateSevenDays() {
    const now = Date.now();
    const readings = [];

    for (let day = 0; day <= 7; day++) {
        readings.push({
            t: now - (7 - day) * 86400000,
            gas_kg: Number((3.0 - day * 0.1).toFixed(2))
        });
    }

    return calculateConsumption(readings);
}

function displayPrediction(prediction) {
    if (!prediction) {
        $("days-left").textContent = "--";
        $("consumption-rate").textContent =
            "Average consumption: unavailable";
        $("prediction-note").textContent =
            "Not enough valid consumption data.";
        return;
    }

    $("days-left").textContent =
        prediction.days.toFixed(1) + " days";

    $("consumption-rate").textContent =
        "Average consumption: " +
        prediction.dailyRate.toFixed(2) + " kg/day";

    $("prediction-note").textContent =
        "Estimate based on simulated daily readings.";
}

// SHORT-TERM SENSOR HISTORY

const HISTORY_LIMIT = 300;
const HISTORY_KEY_PREFIX = "smartLpgHistoryV1_";

const historyStore = {
    demo: [],
    live: []
};

function loadHistory(kind) {
    try {
        const rows = JSON.parse(
            localStorage.getItem(HISTORY_KEY_PREFIX + kind) || "[]"
        );

        if (!Array.isArray(rows)) return [];

        return rows.filter(row =>
            row && finiteNumber(row.t)
        ).slice(-HISTORY_LIMIT);
    } catch (error) {
        return [];
    }
}

function saveHistory(kind) {
    try {
        localStorage.setItem(
            HISTORY_KEY_PREFIX + kind,
            JSON.stringify(historyStore[kind])
        );
    } catch (error) {
        console.warn("History storage unavailable:", error);
    }
}

function addHistorySample(data, kind) {
    const row = {
        t: Date.now(),
        gas_kg: finiteNumber(data.gas_kg) ? data.gas_kg : null,
        mq5_voltage: finiteNumber(data.mq5_voltage)
            ? data.mq5_voltage : null
    };

    if (row.gas_kg === null && row.mq5_voltage === null) return;

    historyStore[kind].push(row);
    historyStore[kind] = historyStore[kind].slice(-HISTORY_LIMIT);

    saveHistory(kind);
    recordLongTermSample(data, kind);

    if (source === kind) drawHistory();
}

// HISTORY GRAPH

function drawHistory() {
    const canvas = $("history-chart");
    const container = canvas.parentElement;
    const width = Math.max(300, container.clientWidth);
    const height = 270;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);

    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    const key = $("history-metric").value;
    const all = historyStore[source];
    const samples = all.filter(row => finiteNumber(row[key]));

    $("sample-btn").disabled = source !== "demo";

    $("history-info").textContent =
        `${all.length} saved ${source} samples. ` +
        (source === "demo"
            ? "Simulated data."
            : "Live browser-recorded data.");

    ctx.font = "12px Arial";
    ctx.fillStyle = "#64748b";

    if (!samples.length) {
        ctx.fillText("No valid readings recorded yet.", 24, 135);
        return;
    }

    const left = 58;
    const right = 18;
    const top = 23;
    const bottom = 45;
    const plotWidth = width - left - right;
    const plotHeight = height - top - bottom;

    const values = samples.map(row => row[key]);
    let min = Math.min(...values);
    let max = Math.max(...values);

    const padding = Math.max(
        (max - min) * 0.15,
        key === "gas_kg" ? 0.1 : 0.05
    );

    min = Math.max(0, min - padding);
    max += padding;
    if (max === min) max = min + 1;

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
            ((t - firstTime) / (lastTime - firstTime)) *
            plotWidth;
    }

    function pointY(value) {
        return top +
            ((max - value) / (max - min)) * plotHeight;
    }

    ctx.strokeStyle = "#e4ece7";
    ctx.lineWidth = 1;

    for (let i = 0; i <= 4; i++) {
        const y = top + i * plotHeight / 4;
        ctx.beginPath();
        ctx.moveTo(left, y);
        ctx.lineTo(width - right, y);
        ctx.stroke();

        const tick = max - i * (max - min) / 4;
        ctx.fillStyle = "#64748b";
        ctx.fillText(tick.toFixed(2), 8, y + 4);
    }

    ctx.strokeStyle =
        key === "gas_kg" ? "#15803d" : "#2563eb";
    ctx.lineWidth = 2;
    ctx.beginPath();

    samples.forEach((row, index) => {
        const x = pointX(row.t, index);
        const y = pointY(row[key]);

        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });

    ctx.stroke();

    samples.forEach((row, index) => {
        const x = pointX(row.t, index);
        const y = pointY(row[key]);
        ctx.beginPath();
        ctx.arc(x, y, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = ctx.strokeStyle;
        ctx.fill();
    });

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

// CSV EXPORT

function exportHistory() {
    const rows = historyStore[source];

    if (!rows.length) {
        alert("No history to export yet.");
        return;
    }

    const lines = ["timestamp,gas_kg,mq5_voltage"];

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
    link.download = `smart-lpg-${source}-history.csv`;
    link.click();

    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// LPG COST CALCULATOR

const LPG_PRICE_KEY = "smartLpgPricePerKg";
let lpgPricePerKg = null;

try {
    const savedPrice = localStorage.getItem(LPG_PRICE_KEY);

    if (savedPrice !== null && savedPrice !== "") {
        const parsed = Number(savedPrice);

        if (Number.isFinite(parsed) && parsed >= 0) {
            lpgPricePerKg = parsed;
            $("lpg-price").value = parsed;
        }
    }
} catch (error) {
    console.warn("Unable to load LPG price:", error);
}

function updateCosts(data) {
    const remaining = data.gas_kg;

    if (
        !finiteNumber(remaining) ||
        remaining < 0 ||
        remaining > LPG_CAPACITY_KG
    ) {
        $("cost-gas-kg").textContent = "-- kg";
        $("cost-used-kg").textContent = "-- kg";
        $("remaining-cost").textContent = "Rs. --";
        $("used-cost").textContent = "Rs. --";
        $("refill-cost").textContent = "Rs. --";

        $("used-gas-info").textContent =
            "Requires valid weight data.";

        $("refill-gas-info").textContent =
            "Cost to refill to 3 kg.";
    } else {
        const used = LPG_CAPACITY_KG - remaining;

        $("cost-gas-kg").textContent =
            remaining.toFixed(2) + " kg";

        $("cost-used-kg").textContent =
            used.toFixed(2) + " kg";

        $("used-gas-info").textContent =
            used.toFixed(2) + " kg missing from a full container.";

        $("refill-gas-info").textContent =
            used.toFixed(2) + " kg required to refill.";

        $("remaining-cost").textContent =
            lpgPricePerKg === null
                ? "Rs. --"
                : formatPKR(remaining * lpgPricePerKg);

        $("used-cost").textContent =
            lpgPricePerKg === null
                ? "Rs. --"
                : formatPKR(used * lpgPricePerKg);

        $("refill-cost").textContent =
            lpgPricePerKg === null
                ? "Rs. --"
                : formatPKR(used * lpgPricePerKg);
    }

    $("full-refill-cost").textContent =
        lpgPricePerKg === null
            ? "Rs. --"
            : formatPKR(LPG_CAPACITY_KG * lpgPricePerKg);
}

$("lpg-price").addEventListener("input", () => {
    const value = $("lpg-price").value.trim();

    if (
        value === "" ||
        !Number.isFinite(Number(value)) ||
        Number(value) < 0
    ) {
        lpgPricePerKg = null;
        try {
            localStorage.removeItem(LPG_PRICE_KEY);
        } catch (error) {
            console.warn("Storage unavailable:", error);
        }
    } else {
        lpgPricePerKg = Number(value);
        try {
            localStorage.setItem(
                LPG_PRICE_KEY,
                String(lpgPricePerKg)
            );
        } catch (error) {
            console.warn("Storage unavailable:", error);
        }
    }

    updateCosts(currentCostData);
    updateSessionDisplay();
});

// LONG-TERM CONSUMPTION TRACKING

const LONG_TERM_PREFIX = "smartLpgLongTermV1_";
const SNAPSHOT_INTERVAL_MS = 60 * 60 * 1000;
const RETENTION_MS = 60 * 24 * 60 * 60 * 1000;
const ONE_DAY_MS = 24 * 60 * 60 * 1000;
const REFILL_THRESHOLD_KG = 0.15;
const MIN_CONSUMPTION_KG = 0.03;

const longTermStore = {
    demo: [],
    live: []
};

function loadLongTerm(kind) {
    try {
        const rows = JSON.parse(
            localStorage.getItem(
                LONG_TERM_PREFIX + kind
            ) || "[]"
        );

        if (!Array.isArray(rows)) return [];

        const now = Date.now();
        const cutoff = now - RETENTION_MS;

        return rows.filter(row =>
            row &&
            Number.isFinite(row.t) &&
            Number.isFinite(row.gas_kg) &&
            row.gas_kg >= 0 &&
            row.gas_kg <= LPG_CAPACITY_KG &&
            row.t >= cutoff &&
            row.t <= now
        ).sort((a, b) => a.t - b.t);

    } catch (error) {
        return [];
    }
}

function saveLongTerm(kind) {
    try {
        localStorage.setItem(
            LONG_TERM_PREFIX + kind,
            JSON.stringify(longTermStore[kind])
        );
    } catch (error) {
        console.warn("Long-term storage unavailable:", error);
    }
}

function recordLongTermSample(data, kind) {
    const weight = data.gas_kg;

    if (
        !finiteNumber(weight) ||
        weight < 0 ||
        weight > LPG_CAPACITY_KG
    ) return;

    const now = Date.now();
    let rows = longTermStore[kind];
    const last = rows[rows.length - 1];

    if (last) {
        const increase = weight - last.gas_kg;

        if (increase >= REFILL_THRESHOLD_KG) {
            // Likely refill: reset history.
            rows = [];
        } else if (now - last.t < SNAPSHOT_INTERVAL_MS) {
            return;
        }
    }

    rows.push({ t: now, gas_kg: weight });

    const cutoff = now - RETENTION_MS;
    longTermStore[kind] = rows.filter(
        row => row.t >= cutoff
    );

    saveLongTerm(kind);

    if (kind === "live" && source === "live") {
        showLivePrediction(data);
    }
}

function calculateLongTermConsumption(readings) {
    if (!Array.isArray(readings)) return null;

    const valid = readings.filter(row =>
        row &&
        Number.isFinite(row.t) &&
        Number.isFinite(row.gas_kg) &&
        row.gas_kg >= 0 &&
        row.gas_kg <= LPG_CAPACITY_KG
    ).sort((a, b) => a.t - b.t);

    if (valid.length < 2) return null;

    let segmentStart = 0;

    for (let i = 1; i < valid.length; i++) {
        if (
            valid[i].gas_kg - valid[i - 1].gas_kg >=
            REFILL_THRESHOLD_KG
        ) {
            segmentStart = i;
        }
    }

    const segment = valid.slice(segmentStart);
    if (segment.length < 2) return null;

    const first = segment[0];
    const last = segment[segment.length - 1];
    const elapsedDays = (last.t - first.t) / ONE_DAY_MS;

    if (elapsedDays < 1) return null;

    const consumed = first.gas_kg - last.gas_kg;
    if (consumed < MIN_CONSUMPTION_KG) return null;

    const dailyRate = consumed / elapsedDays;
    if (dailyRate <= 0) return null;

    return {
        dailyRate,
        days: last.gas_kg / dailyRate,
        consumed,
        elapsedDays
    };
}

function showLivePrediction(data) {
    if (!finiteNumber(data.gas_kg)) {
        $("days-left").textContent = "--";
        $("consumption-rate").textContent =
            "Average consumption: unavailable";
        $("prediction-note").textContent =
            "Waiting for valid live weight readings.";
        return;
    }

    const prediction = calculateLongTermConsumption(
        longTermStore.live
    );

    if (!prediction) {
        $("days-left").textContent = "--";
        $("consumption-rate").textContent =
            "Average consumption: unavailable";
        $("prediction-note").textContent =
            "Requires at least 24 hours of valid weight history after the last refill.";
        return;
    }

    $("days-left").textContent =
        prediction.days.toFixed(1) + " days";

    $("consumption-rate").textContent =
        "Average consumption: " +
        prediction.dailyRate.toFixed(2) + " kg/day";

    $("prediction-note").textContent =
        "Calculated from " +
        prediction.elapsedDays.toFixed(1) +
        " days of recorded weight data. Experimental estimate.";
}

// DASHBOARD DISPLAY

function render(data) {
    const percent = finiteNumber(data.gas_percent)
        ? Math.max(0, Math.min(100, data.gas_percent))
        : null;

    $("gas-kg").textContent =
        valueOrDash(data.gas_kg, 2, " kg");

    $("cylinder-percent").textContent =
        percent === null ? "--%" : Math.round(percent) + "%";

    $("cylinder-fill").style.height =
        (percent === null ? 0 : percent) + "%";

    if (source === "demo") {
        displayPrediction(demoPrediction);
    } else if (data.simulated === true) {
        displayPrediction(null);
        $("prediction-note").textContent =
            "Live predictions unavailable for simulated API data.";
    } else {
        showLivePrediction(data);
    }

    $("mq5-reading").textContent =
        valueOrDash(data.mq5_voltage, 2, " V");

    $("mq5-status").textContent =
        "Status: " +
        (typeof data.gas_status === "string"
            ? data.gas_status.replaceAll("_", " ")
            : "unavailable");

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

    currentCostData = data;
    updateCosts(data);
    updateSessionDisplay();
}

// LIVE PICO API

async function refreshLive() {
    if (source !== "live" || inflight) return;

    const url = $("api-url").value.trim();

    if (!/^https?:\/\//i.test(url)) {
        showStatus("Invalid API URL", "error");
        return;
    }

    if (
        window.location.protocol === "https:" &&
        /^http:\/\//i.test(url)
    ) {
        showStatus(
            "BLOCKED — HTTPS/HTTP mismatch",
            "error"
        );
        $("last-update").textContent =
            "Open the dashboard locally over HTTP to connect to the Pico, or serve the API through HTTPS.";
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
            throw new Error("HTTP " + response.status);
        }

        const data = await response.json();

        if (
            !data ||
            typeof data !== "object" ||
            !("gas_status" in data)
        ) {
            throw new Error("Unexpected API response");
        }

        if (
            source !== "live" ||
            requestController !== controller
        ) return;

        render(data);

        if (data.simulated !== true) {
            addHistorySample(data, "live");
        }

        if (data.simulated === true) {
            showStatus("MOCK — Simulated Pico connected", "demo");
        } else {
            showStatus("LIVE — Pico connected", "live");
        }
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

// DEMO / LIVE SWITCHING

function setSource(next) {
    source = next;

    if (requestController) {
        requestController.abort();
    }

    $("api-url").disabled = next !== "live";
    $("demo-controls").hidden = next !== "demo";
    $("simulate-usage-btn").hidden = next !== "demo";

    if (next === "demo") {
        render(demoCurrentData);
        drawHistory();
        showStatus("DEMO — simulated data");
        $("last-update").textContent =
            "Simulated readings only.";
    } else {
        render(demoSamples.fault);
        drawHistory();
        showStatus("CONNECTING — waiting for Pico");
        $("last-update").textContent =
            "Attempting to fetch live readings...";
        refreshLive();
    }

    updateSessionDisplay();
}

// COOKING SESSION TRACKING

const SESSION_KEY = "smartLpgCookingSessionsV1";
let activeSession = null;
let savedSessions = [];

try {
    const stored = JSON.parse(
        localStorage.getItem(SESSION_KEY) || "[]"
    );
    if (Array.isArray(stored)) savedSessions = stored;
} catch (error) {
    console.warn("Could not load cooking sessions:", error);
}

function saveSessions() {
    try {
        localStorage.setItem(
            SESSION_KEY,
            JSON.stringify(savedSessions)
        );
    } catch (error) {
        console.warn("Could not save sessions:", error);
        $("session-message").textContent =
            "Session saved in memory only; browser storage unavailable.";
    }
}

function formatSessionDuration(milliseconds) {
    const total = Math.max(
        0,
        Math.floor(milliseconds / 1000)
    );

    const hours = String(
        Math.floor(total / 3600)
    ).padStart(2, "0");

    const minutes = String(
        Math.floor((total % 3600) / 60)
    ).padStart(2, "0");

    const seconds = String(total % 60).padStart(2, "0");

    return `${hours}:${minutes}:${seconds}`;
}

function getCurrentSessionWeight() {
    const weight = currentCostData.gas_kg;
    if (source === "live" && currentCostData.simulated === true) {
        return null;
    }

    if (
        !finiteNumber(weight) ||
        weight < 0 ||
        weight > LPG_CAPACITY_KG
    ) return null;

    return weight;
}

function updateSessionDisplay() {
    const isActive = activeSession !== null;

    $("start-session-btn").disabled =
        isActive || getCurrentSessionWeight() === null;    $("end-session-btn").disabled = !isActive;
    $("simulate-cooking-btn").disabled =
        !isActive || source !== "demo";

    $("session-status").textContent = isActive
        ? "Cooking session in progress"
        : "No active session";

    document.querySelector(
        ".session-status-box"
    ).classList.toggle("active", isActive);

    if (!isActive) {
        $("session-timer").textContent = "00:00:00";
        $("session-start-weight").textContent = "-- kg";
        $("session-current-weight").textContent = "-- kg";
        $("session-usage").textContent = "-- kg";
        $("session-cost").textContent = "Rs. --";
        return;
    }

    const elapsed = Date.now() - activeSession.startedAt;

    $("session-timer").textContent =
        formatSessionDuration(elapsed);

    $("session-start-weight").textContent =
        activeSession.startKg.toFixed(2) + " kg";

    const current = getCurrentSessionWeight();

    if (current === null) {
        $("session-current-weight").textContent = "-- kg";
        $("session-usage").textContent = "-- kg";
        $("session-cost").textContent = "Rs. --";
        return;
    }

    const used = Math.max(
        0,
        activeSession.startKg - current
    );

    $("session-current-weight").textContent =
        current.toFixed(2) + " kg";

    $("session-usage").textContent =
        used.toFixed(2) + " kg";

    $("session-cost").textContent =
        lpgPricePerKg === null
            ? "Rs. --"
            : formatPKR(used * lpgPricePerKg);
}

function startCookingSession() {
    if (activeSession) return;

    const weight = getCurrentSessionWeight();

    if (weight === null) {
        $("session-message").textContent =
            "Cannot start: a valid LPG weight is required.";
        return;
    }

    activeSession = {
        startedAt: Date.now(),
        startKg: weight,
        source
    };

    $("session-message").textContent =
        source === "demo"
            ? "Demo session started. Use the simulation button."
            : "Live session started. Waiting for weight changes.";

    updateSessionDisplay();
}

function endCookingSession() {
    if (!activeSession) return;

    if (source !== activeSession.source) {
        $("session-message").textContent =
            "Data source changed. Session cannot finish.";
        return;
    }

    const endingWeight = getCurrentSessionWeight();

    if (endingWeight === null) {
        $("session-message").textContent =
            "Cannot finish: current weight is unavailable.";
        return;
    }

    if (endingWeight > activeSession.startKg) {
        $("session-message").textContent =
            "Weight increased. Check for refilling or measurement error.";
        return;
    }

    const endedAt = Date.now();
    const usedKg = Math.max(
        0,
        activeSession.startKg - endingWeight
    );

    const price = lpgPricePerKg;

    const record = {
        startedAt: activeSession.startedAt,
        endedAt,
        durationMs: endedAt - activeSession.startedAt,
        startKg: activeSession.startKg,
        endKg: endingWeight,
        usedKg,
        pricePerKg: price,
        cost: price === null ? null : usedKg * price,
        source: activeSession.source
    };

    savedSessions.unshift(record);
    savedSessions = savedSessions.slice(0, 100);

    saveSessions();
    activeSession = null;

    $("session-message").textContent =
        "Session completed and saved.";

    updateSessionDisplay();
    renderSessionHistory();
}

function simulateCookingUse() {
    if (!activeSession || source !== "demo") return;

    const current = getCurrentSessionWeight();
    if (current === null) return;

    if (current <= 0) {
        $("session-message").textContent =
            "Simulated LPG is already empty.";
        return;
    }

    const newWeight = Math.max(
        0,
        Number((current - 0.1).toFixed(2))
    );

    const newPercent = Number(
        ((newWeight / LPG_CAPACITY_KG) * 100).toFixed(1)
    );

    const simulated = {
        ...currentCostData,
        gas_kg: newWeight,
        gas_percent: newPercent,
        days_left: null,
        low_gas: newPercent <= 20,
        alert_state: currentCostData.leak === true
            ? "LEAK_DETECTED"
            : newPercent <= 20
                ? "LOW_GAS"
                : "NORMAL"
    };

    demoCurrentData = simulated;

    // Keep prediction consistent with remaining gas.
    if (demoPrediction && demoPrediction.dailyRate > 0) {
        demoPrediction = {
            dailyRate: demoPrediction.dailyRate,
            days: newWeight / demoPrediction.dailyRate
        };
    }

    render(simulated);
    addHistorySample(simulated, "demo");
    updateSessionDisplay();

    $("session-message").textContent =
        "Simulated 0.10 kg of LPG consumption.";
}

function renderSessionHistory() {
    const container = $("session-history");
    container.replaceChildren();

    if (savedSessions.length === 0) {
        const p = document.createElement("p");
        p.textContent =
            "No cooking sessions recorded yet.";
        container.appendChild(p);
        return;
    }

    savedSessions.forEach((session, index) => {
        const card = document.createElement("div");
        card.className = "session-record";

        const heading = document.createElement("h3");
        heading.textContent =
            `Session ${savedSessions.length - index} — ` +
            new Date(session.startedAt).toLocaleString();
        card.appendChild(heading);

        const details = [
            ["Mode", session.source === "demo" ? "Demo" : "Live"],
            ["Duration", formatSessionDuration(session.durationMs)],
            ["Starting LPG", session.startKg.toFixed(2) + " kg"],
            ["Ending LPG", session.endKg.toFixed(2) + " kg"],
            ["LPG Used", session.usedKg.toFixed(2) + " kg"],
            [
                "Session Cost",
                session.cost === null
                    ? "Rs. --"
                    : formatPKR(session.cost)
            ]
        ];

        details.forEach(([label, value]) => {
            const p = document.createElement("p");
            p.textContent = `${label}: ${value}`;
            card.appendChild(p);
        });

        container.appendChild(card);
    });
}

function cancelCookingSession(reason) {
    if (!activeSession) return;
    activeSession = null;
    $("session-message").textContent = reason;
    updateSessionDisplay();
}

// TAB NAVIGATION

const tabButtons = document.querySelectorAll(".tab-button");
const tabPanels = document.querySelectorAll(".tab-panel");

function switchTab(tabName) {
    tabButtons.forEach(button => {
        const isActive = button.dataset.tab === tabName;
        button.classList.toggle("active", isActive);
        button.setAttribute("aria-selected", String(isActive));
    });

    tabPanels.forEach(panel => {
        panel.hidden = panel.id !== "tab-" + tabName;
    });

    if (tabName === "history") drawHistory();
}

// EVENT LISTENERS

document.querySelectorAll('input[name="source"]').forEach(radio => {
    radio.addEventListener("change", () => {
        if (!radio.checked) return;

        cancelCookingSession(
            "Session cancelled because the data source changed."
        );

        setSource(radio.value);
    });
});

document.querySelectorAll("[data-demo]").forEach(button => {
    button.addEventListener("click", () => {
        cancelCookingSession(
            "Session cancelled because the demo scenario changed."
        );

        demoChoice = button.dataset.demo;
        demoCurrentData = { ...demoSamples[demoChoice] };
        demoPrediction = null;

        if (source === "demo") {
            render(demoCurrentData);
            addHistorySample(demoCurrentData, "demo");
        }
    });
});

$("refresh-btn").addEventListener("click", () => {
    if (source === "live") {
        refreshLive();
    } else {
        render(demoCurrentData);
    }
});

$("history-metric").addEventListener("change", drawHistory);

$("sample-btn").addEventListener("click", () => {
    if (source === "demo") {
        addHistorySample(demoCurrentData, "demo");
    }
});

$("csv-btn").addEventListener("click", exportHistory);

$("clear-history-btn").addEventListener("click", () => {
    if (!confirm(`Clear all ${source} history?`)) return;

    historyStore[source] = [];
    saveHistory(source);
    drawHistory();
});

$("simulate-usage-btn").addEventListener("click", () => {
    if (source !== "demo") return;

    if (activeSession) {
        $("prediction-note").textContent =
            "Finish the cooking session before simulating seven days.";
        return;
    }

    demoPrediction = simulateSevenDays();

    demoCurrentData = {
        ...demoSamples.normal,
        gas_kg: 2.3,
        gas_percent: Number(
            (2.3 / LPG_CAPACITY_KG * 100).toFixed(1)
        )
    };

    render(demoCurrentData);
    addHistorySample(demoCurrentData, "demo");
});

$("start-session-btn").addEventListener(
    "click", startCookingSession
);

$("end-session-btn").addEventListener(
    "click", endCookingSession
);

$("simulate-cooking-btn").addEventListener(
    "click", simulateCookingUse
);

$("clear-sessions-btn").addEventListener("click", () => {
    if (!confirm("Delete all saved cooking sessions?")) return;

    savedSessions = [];
    saveSessions();
    renderSessionHistory();
});

tabButtons.forEach(button => {
    button.addEventListener("click", () => {
        switchTab(button.dataset.tab);
    });
});

window.addEventListener("resize", drawHistory);

// INITIALIZATION

for (const kind of ["demo", "live"]) {
    historyStore[kind] = loadHistory(kind);
    longTermStore[kind] = loadLongTerm(kind);
}

renderSessionHistory();
updateSessionDisplay();

switchTab("monitor");
setSource("demo");

setInterval(() => {
    if (source === "live") {
        refreshLive();
    }
}, 2000);

setInterval(updateSessionDisplay, 1000);
