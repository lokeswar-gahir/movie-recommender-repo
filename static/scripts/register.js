document.getElementById("registrationForm").addEventListener("submit", function (ev) {
    const password = document.getElementById("password");
    const confirmPassword = document.getElementById("confirmPassword");
    if (password.value !== confirmPassword.value) {
        ev.preventDefault();
        alert("Passwords do not match! Please re-enter your password.");
        password.value = "";
        confirmPassword.value = "";
        return false;
    }
    const termsCheckbox = document.getElementById("termsCheckbox");
    if (!termsCheckbox.checked) {
        ev.preventDefault();
        alert("Please agree to the Terms and Conditions to proceed.");
        return false;
    }
    return true;
})

const pswdBtn = document.getElementById("show-hide-pswd")
pswdBtn.addEventListener("click", function () {
    if (pswdBtn.innerText === "Show") {
        pswdBtn.innerText = "Hide";
        document.getElementById("password").setAttribute("type", "text");
    } else {
        pswdBtn.innerText = "Show";
        document.getElementById("password").setAttribute("type", "password");
    }
})
const cpswdBtn = document.getElementById("show-hide-cpswd")
cpswdBtn.addEventListener("click", function () {
    if (cpswdBtn.innerText === "Show") {
        cpswdBtn.innerText = "Hide";
        document.getElementById("confirmPassword").setAttribute("type", "text");
    } else {
        cpswdBtn.innerText = "Show";
        document.getElementById("confirmPassword").setAttribute("type", "password");
    }
})
