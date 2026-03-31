var toggleChangePassword = document.getElementById("toggleChangePassword");
var changePasswordForm = document.querySelector(".change-password-form");
var changePasswordHeader = document.querySelector(".change-password-header");

toggleChangePassword.addEventListener("click", function () {
    if (changePasswordForm.style.display === "flex") {
        changePasswordForm.style.display = "none";
        changePasswordHeader.style.display = "none";
    } else {
        changePasswordForm.style.display = "flex";
        changePasswordHeader.style.display = "block";
    }
});