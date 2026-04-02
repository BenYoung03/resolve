document.addEventListener("DOMContentLoaded", function () {

    const filterButtons = document.querySelectorAll(".activity-filter");
    const activityItems = document.querySelectorAll(".activity-item");

    function applyFilter(filter) {
        activityItems.forEach(item => {
            const itemType = item.dataset.type;
            if (filter === "all" || itemType === filter) {
                item.style.display = "";
            } else {
                item.style.display = "none";
            }
        });

        filterButtons.forEach(button => {
            button.classList.toggle("active", button.dataset.filter === filter);
        });
    }

    filterButtons.forEach(button => {
        button.addEventListener("click", function () {
            applyFilter(this.dataset.filter);
        });
    });

    var resolutionText = document.querySelector(".resolution-reasoning-input");
    var resolutionLabel = document.querySelector(".resolution-reasoning-label");
    var statusSelect = document.getElementById("status-select");
    var assignedSelect = document.getElementById("assigned-select");

    if (!statusSelect || !assignedSelect || !resolutionText || !resolutionLabel) {
        return;
    }

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
    assignedSelect.addEventListener("change", function () {
        var isUnassigned = this.value === "0";

        if (isUnassigned) {
            statusSelect.value = "1";
        } else if (statusSelect.value === "1") {
            statusSelect.value = "2";
        }

        toggleResolutionReasoning();
    });
});


