let countdownInterval = null;
let currentSeconds = 0;
let currentUnit = "seconds";

document.addEventListener("DOMContentLoaded", () => {
    const body = document.body;
    const mode = body.dataset.mode;

    initSettings();

    if (mode) {
        startCountdown(mode);
    }
});

function initSettings() {
    const savedTheme = localStorage.getItem("countdownTheme") || "green";
    currentUnit = "seconds";

    applyTheme(savedTheme);
    setActiveOption(".color-option", "theme", savedTheme);
    setCountdownUnit(currentUnit);

    document.getElementById("settings-toggle").addEventListener("click", openSettings);
    document.getElementById("settings-close").addEventListener("click", closeSettings);
    document.getElementById("coming-soon-close").addEventListener("click", closeComingSoon);

    document.querySelectorAll(".campus-option").forEach(button => {
        button.addEventListener("click", () => showComingSoon(button.dataset.campus));
    });

    document.querySelectorAll(".unit-option").forEach(button => {
        button.addEventListener("click", () => {
            setCountdownUnit(button.dataset.unit);
        });
    });

    document.querySelectorAll(".color-option").forEach(button => {
        button.addEventListener("click", () => {
            applyTheme(button.dataset.theme);
            localStorage.setItem("countdownTheme", button.dataset.theme);
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
    fetch(`/api/countdown/${mode}`)
        .then(response => response.json())
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
    const display = getDisplayValue(currentSeconds, currentUnit);
    document.getElementById("countdown").textContent = display.value;
    document.getElementById("countdown-unit").textContent = display.label;
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
    document.getElementById("settings-panel").hidden = false;
    document.getElementById("settings-toggle").setAttribute("aria-expanded", "true");
}

function closeSettings() {
    document.getElementById("settings-panel").hidden = true;
    document.getElementById("settings-toggle").setAttribute("aria-expanded", "false");
}

function showComingSoon(campus) {
    document.getElementById("coming-soon-text").textContent =
        `${campus} wird später freigeschaltet. Countdown bleibt unverändert.`;
    document.getElementById("coming-soon-overlay").hidden = false;
}

function closeComingSoon() {
    document.getElementById("coming-soon-overlay").hidden = true;
}

function setCountdownUnit(unit) {
    currentUnit = unit || "seconds";
    setActiveOption(".unit-option", "unit", currentUnit);
    updateCountdownDisplay();
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
