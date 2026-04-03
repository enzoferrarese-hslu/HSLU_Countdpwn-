let countdownInterval = null;
let currentSeconds = 0;

function startCountdown(mode) {
    fetch(`/api/countdown/${mode}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById("status-message").textContent = data.error;
                return;
            }

            document.getElementById("semester-name").textContent = `Semester: ${data.semester_name}`;

            if (mode === "contact") {
                document.getElementById("target-date").textContent =
                    `Ziel: Ende Kontaktstudium (${data.target_date})`;
            } else {
                document.getElementById("target-date").textContent =
                    `Ziel: Ende Prüfungsphase (${data.target_date})`;
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
                    document.getElementById("status-message").textContent =
                        "Der Countdown ist abgelaufen.";
                    return;
                }

                updateCountdownDisplay();
            }, 1000);

            document.getElementById("status-message").textContent =
                "Countdown läuft...";
        })
        .catch(error => {
            document.getElementById("status-message").textContent =
                "Fehler beim Laden des Countdowns.";
            console.error(error);
        });
}

function updateCountdownDisplay() {
    document.getElementById("countdown").textContent = currentSeconds.toLocaleString("de-CH");
}