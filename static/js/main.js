// AquaAI Production JavaScript Engine & Component Handlers

// Global Toast Notification Function
function showToast(title, message, type = "success", duration = 4000) {
    let container = document.querySelector(".toast-container-custom");
    if (!container) {
        container = document.createElement("div");
        container.className = "toast-container-custom";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast-custom toast-${type}`;

    let iconClass = "fa-circle-check text-success";
    if (type === "error") iconClass = "fa-circle-exclamation text-danger";
    if (type === "warning") iconClass = "fa-triangle-exclamation text-warning";
    if (type === "info") iconClass = "fa-circle-info text-info";

    toast.innerHTML = `
        <i class="fa-solid ${iconClass} fs-5 mt-1"></i>
        <div class="flex-grow-1">
            <div class="fw-bold small text-dark">${title}</div>
            <div class="text-muted small">${message}</div>
        </div>
        <button type="button" class="btn-close btn-sm ms-2" onclick="this.parentElement.remove()"></button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Animate Circular WQS Gauge Score & Number Counter
function animateWqsGauge(targetScore) {
    const gaugeFill = document.querySelector(".gauge-fill");
    const scoreVal = document.getElementById("gaugeScoreValue");

    if (!gaugeFill || !scoreVal) return;

    // Circumference of r=60 circle is 2 * PI * 60 = 376.99 (rounded to 377)
    const maxOffset = 377;
    const targetOffset = maxOffset - (maxOffset * (targetScore / 100));

    // Color based on score range
    let strokeColor = "#10B981"; // Emerald
    if (targetScore < 50) strokeColor = "#EF4444"; // Red
    else if (targetScore < 70) strokeColor = "#F59E0B"; // Amber
    else if (targetScore < 85) strokeColor = "#0284C7"; // Cyan/Blue

    gaugeFill.style.stroke = strokeColor;
    gaugeFill.style.strokeDashoffset = targetOffset;

    // Number counter animation
    let current = 0;
    const duration = 1200; // ms
    const stepTime = 20;
    const steps = duration / stepTime;
    const increment = targetScore / steps;

    const timer = setInterval(() => {
        current += increment;
        if (current >= targetScore) {
            current = targetScore;
            clearInterval(timer);
        }
        scoreVal.textContent = current.toFixed(1);
    }, stepTime);
}

document.addEventListener("DOMContentLoaded", function () {
    // 1. Password Visibility Toggle
    const toggleButtons = document.querySelectorAll(".toggle-password");
    toggleButtons.forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            e.preventDefault();
            const targetId = btn.getAttribute("data-target");
            const input = document.getElementById(targetId);
            const icon = btn.querySelector("i");

            if (input && icon) {
                if (input.type === "password") {
                    input.type = "text";
                    icon.classList.remove("fa-eye");
                    icon.classList.add("fa-eye-slash");
                } else {
                    input.type = "password";
                    icon.classList.remove("fa-eye-slash");
                    icon.classList.add("fa-eye");
                }
            }
        });
    });

    // 2. Registration Modal Handlers
    const btnSwitchToLogin = document.getElementById("btnSwitchToLogin");
    const btnCloseRegModal = document.getElementById("btnCloseRegModal");
    const regModal = document.getElementById("regSuccessModal");

    if (btnSwitchToLogin && regModal) {
        btnSwitchToLogin.addEventListener("click", function () {
            regModal.classList.remove("d-block");
            regModal.classList.add("d-none");
            const loginTabBtn = document.getElementById("login-tab");
            if (loginTabBtn) new bootstrap.Tab(loginTabBtn).show();
        });
    }

    if (btnCloseRegModal && regModal) {
        btnCloseRegModal.addEventListener("click", function () {
            regModal.classList.remove("d-block");
            regModal.classList.add("d-none");
        });
    }

    // 3. Security Question Reset Step-Indicator Manager
    const resetInitForm = document.getElementById("resetInitForm");
    const resetVerifyForm = document.getElementById("resetVerifyForm");
    const resetConfirmForm = document.getElementById("resetConfirmForm");

    const resetStep1 = document.getElementById("resetStep1");
    const resetStep2 = document.getElementById("resetStep2");
    const resetStep3 = document.getElementById("resetStep3");
    const resetStep4 = document.getElementById("resetStep4");

    const stepPill1 = document.getElementById("stepPill1");
    const stepPill2 = document.getElementById("stepPill2");
    const stepPill3 = document.getElementById("stepPill3");

    if (resetInitForm) {
        resetInitForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const emailInput = document.getElementById("reset_email");
            const email = emailInput ? emailInput.value.trim() : "";

            if (!email.toLowerCase().endsWith("@gmail.com")) {
                showToast("Invalid Email", "Please enter a valid Gmail address (@gmail.com).", "error");
                return;
            }

            const btn = document.getElementById("btnResetInit");
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Checking...`;
            }

            fetch(resetInitForm.action, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: new URLSearchParams({ email: email })
            })
            .then(res => res.json())
            .then(data => {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = `<i class="fa-solid fa-arrow-right me-1"></i> Continue`;
                }
                if (data.success) {
                    document.getElementById("displaySecQuestion").textContent = data.question;
                    resetStep1.classList.add("d-none");
                    resetStep2.classList.remove("d-none");

                    if (stepPill1 && stepPill2) {
                        stepPill1.className = "step-pill completed";
                        stepPill2.className = "step-pill active";
                    }
                } else {
                    showToast("Account Error", data.message, "error");
                }
            })
            .catch(err => {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = `<i class="fa-solid fa-arrow-right me-1"></i> Continue`;
                }
                showToast("Network Error", "Error checking account: " + err, "error");
            });
        });
    }

    if (resetVerifyForm) {
        resetVerifyForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const answerInput = document.getElementById("reset_sec_answer");
            const answer = answerInput ? answerInput.value.trim() : "";

            if (!answer) {
                showToast("Validation Error", "Please enter your security answer.", "error");
                return;
            }

            const btn = document.getElementById("btnResetVerify");
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Verifying...`;
            }

            fetch(resetVerifyForm.action, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: new URLSearchParams({ security_answer: answer })
            })
            .then(res => res.json())
            .then(data => {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = `<i class="fa-solid fa-shield-check me-1"></i> Verify Answer`;
                }
                if (data.success) {
                    showToast("Identity Verified", data.message, "success");
                    resetStep2.classList.add("d-none");
                    resetStep3.classList.remove("d-none");

                    if (stepPill2 && stepPill3) {
                        stepPill2.className = "step-pill completed";
                        stepPill3.className = "step-pill active";
                    }
                } else {
                    showToast("Verification Failed", data.message, "error");
                    if (data.restart) {
                        setTimeout(() => location.reload(), 2000);
                    }
                }
            })
            .catch(err => {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = `<i class="fa-solid fa-shield-check me-1"></i> Verify Answer`;
                }
                showToast("Network Error", "Error verifying security answer: " + err, "error");
            });
        });
    }

    if (resetConfirmForm) {
        resetConfirmForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const newPwd = document.getElementById("new_password_reset").value;
            const confirmPwd = document.getElementById("confirm_password_reset").value;

            if (newPwd !== confirmPwd) {
                showToast("Mismatch Error", "New password and confirm password do not match.", "error");
                return;
            }

            fetch(resetConfirmForm.action, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: new URLSearchParams({ new_password: newPwd, confirm_password: confirmPwd })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    resetStep3.classList.add("d-none");
                    resetStep4.classList.remove("d-none");

                    if (stepPill3) stepPill3.className = "step-pill completed";
                } else {
                    showToast("Reset Error", data.message, "error");
                }
            })
            .catch(err => {
                showToast("Network Error", "Error updating password: " + err, "error");
            });
        });
    }

    const btnRestartReset = document.getElementById("btnRestartReset");
    if (btnRestartReset) {
        btnRestartReset.addEventListener("click", function () {
            resetStep2.classList.add("d-none");
            resetStep3.classList.add("d-none");
            resetStep4.classList.add("d-none");
            resetStep1.classList.remove("d-none");

            if (stepPill1 && stepPill2 && stepPill3) {
                stepPill1.className = "step-pill active";
                stepPill2.className = "step-pill";
                stepPill3.className = "step-pill";
            }
        });
    }

    const btnGoToLogin = document.getElementById("btnGoToLogin");
    if (btnGoToLogin) {
        btnGoToLogin.addEventListener("click", function () {
            const loginTabBtn = document.getElementById("login-tab");
            if (loginTabBtn) new bootstrap.Tab(loginTabBtn).show();
        });
    }

    // 4. Drag & Drop CSV Upload Handler
    const dropZone = document.getElementById("dropZone");
    const csvFileInput = document.getElementById("csv_file");
    const selectedFileName = document.getElementById("selectedFileName");

    if (dropZone && csvFileInput) {
        dropZone.addEventListener("click", () => csvFileInput.click());

        ["dragenter", "dragover"].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZone.classList.add("dragover");
            }, false);
        });

        ["dragleave", "drop"].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZone.classList.remove("dragover");
            }, false);
        });

        dropZone.addEventListener("drop", (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0 && files[0].name.endsWith(".csv")) {
                csvFileInput.files = files;
                if (selectedFileName) selectedFileName.textContent = "Selected: " + files[0].name;
            } else {
                showToast("Invalid File", "Please upload a valid .csv file.", "error");
            }
        });

        csvFileInput.addEventListener("change", () => {
            if (csvFileInput.files.length > 0) {
                if (selectedFileName) selectedFileName.textContent = "Selected: " + csvFileInput.files[0].name;
            }
        });
    }

    // 5. Water Analysis Form Handler
    const waterForm = document.getElementById("waterAnalysisForm");
    const btnLoadSample = document.getElementById("btnLoadSample");
    const btnClearForm = document.getElementById("btnClearForm");
    const btnToggleEditInputs = document.getElementById("btnToggleEditInputs");
    const inputFormContainer = document.getElementById("inputFormContainer");

    if (btnToggleEditInputs && inputFormContainer) {
        btnToggleEditInputs.addEventListener("click", function () {
            inputFormContainer.classList.toggle("d-none");
        });
    }

    const sampleData = {
        ph: "7.20",
        Hardness: "196.30",
        Solids: "14200.00",
        Chloramines: "7.13",
        Sulfate: "333.00",
        Conductivity: "421.00",
        Organic_carbon: "14.10",
        Trihalomethanes: "66.30",
        Turbidity: "3.96"
    };

    if (btnLoadSample) {
        btnLoadSample.addEventListener("click", function () {
            Object.keys(sampleData).forEach(function (key) {
                const field = document.getElementById(key);
                if (field) field.value = sampleData[key];
            });
            showToast("Sample Data Loaded", "Standard laboratory parameters populated.", "info");
        });
    }

    if (btnClearForm && waterForm) {
        btnClearForm.addEventListener("click", function () {
            const inputs = waterForm.querySelectorAll("input[type='number']");
            inputs.forEach(input => input.value = "");
            showToast("Form Cleared", "All parameter inputs cleared.", "info");
        });
    }

    if (waterForm) {
        waterForm.addEventListener("submit", function () {
            const btn = document.getElementById("btnRunAnalysis");
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Analyzing Water...`;
            }
        });
    }
});
