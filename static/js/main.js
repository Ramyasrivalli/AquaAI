// AquaAI Main JavaScript Utilities, Form Handlers, & Interactive Controls
document.addEventListener("DOMContentLoaded", function () {
    // 1. Auto dismiss alert notifications after 5 seconds
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // 2. Password Visibility Toggle
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

    // 3. Toggle Collapsible Input Form on Water Analysis Page
    const btnToggleEditInputs = document.getElementById("btnToggleEditInputs");
    const inputFormContainer = document.getElementById("inputFormContainer");
    if (btnToggleEditInputs && inputFormContainer) {
        btnToggleEditInputs.addEventListener("click", function () {
            inputFormContainer.classList.toggle("d-none");
            if (!inputFormContainer.classList.contains("d-none")) {
                inputFormContainer.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    }

    // 4. Water Analysis Form Handlers (Clear Form, Load Sample, Decimal Validation)
    const form = document.getElementById("waterAnalysisForm");
    const btnLoadSample = document.getElementById("btnLoadSample");
    const btnClearForm = document.getElementById("btnClearForm");

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
                if (field) {
                    field.value = sampleData[key];
                    field.classList.remove("is-invalid");
                }
            });
            if (inputFormContainer && inputFormContainer.classList.contains("d-none")) {
                inputFormContainer.classList.remove("d-none");
            }
        });
    }

    if (btnClearForm) {
        btnClearForm.addEventListener("click", function () {
            if (form) {
                const inputs = form.querySelectorAll("input[type='number']");
                inputs.forEach(function (input) {
                    input.value = "";
                    input.classList.remove("is-invalid");
                });
            }
        });
    }

    if (form) {
        form.addEventListener("submit", function (e) {
            let isValid = true;
            const inputs = form.querySelectorAll("input[type='number'][required]");

            inputs.forEach(function (input) {
                const val = input.value.trim();
                if (val === "" || isNaN(parseFloat(val))) {
                    isValid = false;
                    input.classList.add("is-invalid");
                } else {
                    input.classList.remove("is-invalid");
                }
            });

            if (!isValid) {
                e.preventDefault();
                e.stopPropagation();

                let alertContainer = document.getElementById("formValidationAlert");
                if (!alertContainer) {
                    alertContainer = document.createElement("div");
                    alertContainer.id = "formValidationAlert";
                    alertContainer.className = "alert alert-warning alert-dismissible fade show mt-3 mb-0";
                    alertContainer.role = "alert";
                    alertContainer.innerHTML = `
                        <i class="fa-solid fa-triangle-exclamation me-2"></i>
                        <strong>Please enter valid numerical values for all required water quality parameters.</strong>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    `;
                    form.appendChild(alertContainer);
                }

                const firstInvalid = form.querySelector(".is-invalid");
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
        });
    }
});
