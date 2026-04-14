let countdownInterval = null;
let currentSeconds = 0;
let currentUnit = "seconds";
let currentMode = null;
let countdownLoaded = false;

document.addEventListener("DOMContentLoaded", () => {
    const body = document.body;
    const mode = body.dataset.mode;

    if (mode) {
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
            if (button.dataset.campus === "Technik & Architektur") {
                window.location.href = "/";
                return;
            }

            showComingSoon(button.dataset.campus);
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

    fetch(`/api/countdown/${mode}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Countdown API nicht erreichbar.");
            }

            return response.json();
        })
        .then(data => {
            if (data.error) {
                document.getElementById("target-date").textContent = data.error;
                document.getElementById("status-text").textContent = "Countdown nicht verfügbar";
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
                `${data.semester_name} aus SQLite geladen`;

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
            document.getElementById("target-date").textContent =
                "Fehler beim Laden des Countdowns.";
            document.getElementById("status-text").textContent = "API nicht erreichbar";
            console.error(error);
        });
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
