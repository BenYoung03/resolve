document.addEventListener("DOMContentLoaded", function () {

    const filterButtons = document.querySelectorAll(".activity-filter");
    const activityItems = document.querySelectorAll(".activity-item");

    // Activity filter functionality that loops through each activity item
    function applyFilter(filter) {
        activityItems.forEach(item => {
            const itemType = item.dataset.type;
            // Display item if filter is "all" or matches the item's type, otherwise hide it
            if (filter === "all" || itemType === filter) {
                item.style.display = "";
            } else {
                item.style.display = "none";
            }
        });

        // Ensure the active filter button is visually indicated by toggling the "active" class if the filter matches
        filterButtons.forEach(button => {
            button.classList.toggle("active", button.dataset.filter === filter);
        });
    }

    // Add an event listener to each filter button that applies the corresponding filter when clicked
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

    // If the status is set to resolved, enable the resolution reasoning input
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

        // If the ticket is unassigned, set status to open, if it is being assigned, set status to assigned by default
        if (isUnassigned) {
            statusSelect.value = "1";
        } else if (statusSelect.value === "1") {
            statusSelect.value = "2";
        }

        toggleResolutionReasoning();
    });
});


