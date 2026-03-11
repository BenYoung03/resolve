document.addEventListener("DOMContentLoaded", function () {
    var resolutionText = document.querySelector(".resolution-reasoning-input");
    var resolutionLabel = document.querySelector(".resolution-reasoning-label");
    var statusSelect = document.getElementById("status-select");

    function toggleResolutionReasoning() {
        if (Number(statusSelect.value) === 5) {
            resolutionText.style.display = "block";
            resolutionLabel.style.display = "block";
            resolutionText.required = true;
        } else {
            resolutionText.style.display = "none";
            resolutionLabel.style.display = "none";
            resolutionText.required = false;
        }
    }

    statusSelect.addEventListener("change", toggleResolutionReasoning);
    toggleResolutionReasoning();
});