let countdownInterval = null;
let currentSeconds = 0;
let currentUnit = "seconds";
let currentMode = null;
let currentDepartment = "Technik & Architektur";
let countdownLoaded = false;
const SUPPORTED_DEPARTMENTS = ["Technik & Architektur", "Wirtschaft"];

document.addEventListener("DOMContentLoaded", () => {
    const body = document.body;
    const mode = body.dataset.mode;
    const bodyDepartment = body.dataset.department;

    currentDepartment = getInitialDepartment(bodyDepartment);
    document.body.dataset.department = currentDepartment;

    if (mode) {
        if (!["contact", "exam"].includes(mode)) {
            showErrorState("Ungültiger Modus.");
            initSettings();
            return;
        }

        currentMode = mode;
        startCountdown(mode);
    }

    initSettings();
});

function initSettings() {
    const savedTheme = getStoredValue("countdownTheme", "green");
    currentUnit = "seconds";

    applyTheme(savedTheme);
    setCountdownUnit(currentUnit);
    syncDepartmentLinks();
    setActiveCampus(currentDepartment);

    const settingsToggle = document.getElementById("settings-toggle");
    const settingsClose = document.getElementById("settings-close");
    const comingSoonClose = document.getElementById("coming-soon-close");

    if (settingsToggle) {
        settingsToggle.addEventListener("click", openSettings);
    }

    if (settingsClose) {
        settingsClose.addEventListener("click", closeSettings);
    }

    if (comingSoonClose) {
        comingSoonClose.addEventListener("click", closeComingSoon);
    }

    document.querySelectorAll(".campus-option").forEach(button => {
        button.addEventListener("click", () => {
            const campus = button.dataset.campus;

            if (SUPPORTED_DEPARTMENTS.includes(campus)) {
                setDepartment(campus);
                return;
            }

            showComingSoon(campus);
        });
    });

    document.querySelectorAll(".unit-option").forEach(button => {
        button.addEventListener("click", () => {
            setCountdownUnit(button.dataset.unit);
        });
    });

    document.querySelectorAll(".color-option").forEach(button => {
        button.addEventListener("click", () => {
            applyTheme(button.dataset.theme);
            setStoredValue("countdownTheme", button.dataset.theme);
        });
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape") {
            closeComingSoon();
            closeSettings();
        }
    });
}

function startCountdown(mode) {
    currentMode = mode;

    fetch(buildDepartmentUrl(`/api/countdown/${mode}`))
        .then(response => {
            if (!response.ok) {
                throw new Error(`API nicht erreichbar (Status ${response.status}).`);
            }

            return response.json();
        })
        .then(data => {
            if (data.error) {
                showErrorState(data.error);
                return;
            }

            if (!data.countdown || typeof data.countdown.total_seconds !== "number") {
                showErrorState("Countdown-Daten fehlen oder sind ungültig.");
                return;
            }

            if (!data.target_date || !data.semester_name) {
                showErrorState("Semesterdaten fehlen in der API-Antwort.");
                return;
            }

            const label = mode === "contact" ? "Kontaktstudium" : "Prüfungsphase";
            document.getElementById("mode-label").textContent = `${label.toUpperCase()}_MODE`;

            if (mode === "contact") {
                document.getElementById("target-date").textContent =
                    `Ziel: Kontaktstudium (${data.target_date})`;
            } else {
                document.getElementById("target-date").textContent =
                    `Ziel: Prüfungsphase (${data.target_date})`;
            }

            document.getElementById("status-text").textContent =
                `${data.department_name} · ${data.semester_name} aus SQLite geladen`;

            currentSeconds = data.countdown.total_seconds;
            countdownLoaded = true;
            updateCountdownDisplay();

            if (countdownInterval) {
                clearInterval(countdownInterval);
            }

            countdownInterval = setInterval(() => {
                currentSeconds--;

                if (currentSeconds <= 0) {
                    currentSeconds = 0;
                    updateCountdownDisplay();
                    document.getElementById("status-text").textContent = "Countdown abgeschlossen";
                    clearInterval(countdownInterval);
                    return;
                }

                updateCountdownDisplay();
            }, 1000);
        })
        .catch(error => {
            showErrorState(error.message || "Netzwerkfehler beim Laden des Countdowns.");
            console.error(error);
        });
}

function showErrorState(message) {
    if (countdownInterval) {
        clearInterval(countdownInterval);
        countdownInterval = null;
    }

    countdownLoaded = false;

    const targetLine = document.getElementById("target-date");
    const countdownGrid = document.querySelector(".countdown-grid");
    const statusStrip = document.querySelector(".status-strip");
    const errorState = document.getElementById("error-state");
    const errorDetail = document.getElementById("error-detail");
    const modeLabel = document.getElementById("mode-label");

    if (targetLine) {
        targetLine.hidden = true;
    }

    if (countdownGrid) {
        countdownGrid.hidden = true;
    }

    if (statusStrip) {
        statusStrip.hidden = true;
    }

    if (modeLabel) {
        modeLabel.textContent = "ERROR_MODE";
    }

    if (errorDetail) {
        errorDetail.textContent = message || "Unbekannter Fehler.";
    }

    if (errorState) {
        errorState.hidden = false;
    }
}

function updateCountdownDisplay() {
    const countdownElement = document.getElementById("countdown");
    const unitElement = document.getElementById("countdown-unit");
    const tileElement = countdownElement ? countdownElement.closest(".time-tile") : null;

    if (!countdownElement || !countdownLoaded) {
        return;
    }

    if (currentSeconds <= 0) {
        showCountdownFinished();
        return;
    }

    const display = getDisplayValue(currentSeconds, currentUnit);

    if (tileElement) {
        tileElement.classList.remove("expired");
    }

    countdownElement.textContent = display.value;

    if (unitElement) {
        unitElement.textContent = display.label;
    }
}

function showCountdownFinished() {
    const countdownElement = document.getElementById("countdown");
    const unitElement = document.getElementById("countdown-unit");
    const tileElement = countdownElement ? countdownElement.closest(".time-tile") : null;

    if (!countdownElement) {
        return;
    }

    countdownElement.textContent = currentMode === "exam"
        ? "Prüfungsphase fertig - Geniesst die Ferien"
        : "Kontaktstudium fertig - Viel Erfolg bei den MEP's";

    if (unitElement) {
        unitElement.textContent = "";
    }

    if (tileElement) {
        tileElement.classList.add("expired");
    }
}

function getDisplayValue(seconds, unit) {
    if (unit === "months") {
        return {
            value: formatDecimal(seconds / 2592000),
            label: "Monate",
        };
    }

    if (unit === "weeks") {
        return {
            value: formatDecimal(seconds / 604800),
            label: "Wochen",
        };
    }

    if (unit === "days") {
        return {
            value: formatDecimal(seconds / 86400),
            label: "Tage",
        };
    }

    return {
        value: seconds.toLocaleString("de-CH"),
        label: "Sekunden",
    };
}

function formatDecimal(value) {
    return value.toLocaleString("de-CH", {
        maximumFractionDigits: 2,
        minimumFractionDigits: value < 10 && value > 0 ? 2 : 0,
    });
}

function openSettings() {
    const panel = document.getElementById("settings-panel");
    const toggle = document.getElementById("settings-toggle");

    if (panel) {
        panel.hidden = false;
    }

    if (toggle) {
        toggle.setAttribute("aria-expanded", "true");
    }
}

function closeSettings() {
    const panel = document.getElementById("settings-panel");
    const toggle = document.getElementById("settings-toggle");

    if (panel) {
        panel.hidden = true;
    }

    if (toggle) {
        toggle.setAttribute("aria-expanded", "false");
    }
}

function showComingSoon(campus) {
    const text = document.getElementById("coming-soon-text");
    const overlay = document.getElementById("coming-soon-overlay");

    if (text) {
        text.textContent = `${campus} wird später freigeschaltet. Countdown bleibt unverändert.`;
    }

    if (overlay) {
        overlay.hidden = false;
    }
}

function closeComingSoon() {
    const overlay = document.getElementById("coming-soon-overlay");

    if (overlay) {
        overlay.hidden = true;
    }
}

function setCountdownUnit(unit) {
    currentUnit = unit || "seconds";
    setActiveOption(".unit-option", "unit", currentUnit);

    if (countdownLoaded) {
        updateCountdownDisplay();
    }
}

function applyTheme(theme) {
    const selectedTheme = theme || "green";
    document.body.dataset.theme = selectedTheme;
    setActiveOption(".color-option", "theme", selectedTheme);
}

function setDepartment(department) {
    currentDepartment = department;
    setStoredValue("countdownDepartment", department);
    document.body.dataset.department = department;
    setActiveCampus(department);
    syncDepartmentLinks();

    if (currentMode) {
        window.location.href = buildDepartmentUrl(`/countdown/${currentMode}`);
        return;
    }

    window.location.href = buildDepartmentUrl("/");
}

function getInitialDepartment(bodyDepartment) {
    const storedDepartment = getStoredValue("countdownDepartment", "");
    const department = bodyDepartment || storedDepartment || "Technik & Architektur";
    return SUPPORTED_DEPARTMENTS.includes(department) ? department : "Technik & Architektur";
}

function setActiveCampus(department) {
    setActiveOption(".campus-option", "campus", department);
}

function syncDepartmentLinks() {
    document.querySelectorAll(".countdown-link").forEach(link => {
        const mode = link.dataset.mode;
        if (!mode) {
            return;
        }

        link.href = buildDepartmentUrl(`/countdown/${mode}`);
    });

    const homeLink = document.getElementById("home-link");
    if (homeLink) {
        homeLink.href = buildDepartmentUrl("/");
    }
}

function buildDepartmentUrl(path) {
    const url = new URL(path, window.location.origin);
    url.searchParams.set("department", currentDepartment);
    return `${url.pathname}${url.search}`;
}

function setActiveOption(selector, dataKey, value) {
    document.querySelectorAll(selector).forEach(button => {
        button.classList.toggle("active", button.dataset[dataKey] === value);
    });
}

function getStoredValue(key, fallback) {
    try {
        return localStorage.getItem(key) || fallback;
    } catch (error) {
        return fallback;
    }
}

function setStoredValue(key, value) {
    try {
        localStorage.setItem(key, value);
    } catch (error) {
        console.warn("Einstellung konnte nicht gespeichert werden.", error);
    }
}
