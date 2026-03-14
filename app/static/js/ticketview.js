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

    var assignedSelect = document.getElementById("assigned-select");
    assignedSelect.addEventListener("change", function () {
        var selectedOption = this.options[this.selectedIndex];
        if (selectedOption.value !== "0") {
            var statusSelect = document.getElementById("status-select");
            for (var i = 0; i < statusSelect.options.length; i++) {
                if (selectedOption.value !== "0") {
                for (var i = 0; i < statusSelect.options.length; i++) {
                    if (statusSelect.options[i].value === "1") { 
                        statusSelect.value = "2";
                    }
                }

            }
        }
    }
});
});