let countdownInterval = null;
let currentSeconds = 0;

document.addEventListener("DOMContentLoaded", () => {
    const body = document.body;
    const mode = body.dataset.mode;

    if (mode) {
        startCountdown(mode);
    }
});

function startCountdown(mode) {
    fetch(`/api/countdown/${mode}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById("target-date").textContent = data.error;
                return;
            }

            if (mode === "contact") {
                document.getElementById("target-date").textContent =
                    `Ziel: Kontaktstudium (${data.target_date})`;
            } else {
                document.getElementById("target-date").textContent =
                    `Ziel: Prüfungsphase (${data.target_date})`;
            }

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
                    clearInterval(countdownInterval);
                    return;
                }

                updateCountdownDisplay();
            }, 1000);
        })
        .catch(error => {
            document.getElementById("target-date").textContent =
                "Fehler beim Laden des Countdowns.";
            console.error(error);
        });
}

function updateCountdownDisplay() {
    document.getElementById("countdown").textContent =
        currentSeconds.toLocaleString("de-CH");
}