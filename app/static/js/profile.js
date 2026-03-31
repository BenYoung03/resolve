var toggleChangePassword = document.getElementById("toggleChangePassword");
var changePasswordForm = document.querySelector(".change-password-form");

toggleChangePassword.addEventListener("click", function () {
    if (changePasswordForm.style.display === "flex") {
        changePasswordForm.style.display = "none";
    } else {
        changePasswordForm.style.display = "flex";
    }
});