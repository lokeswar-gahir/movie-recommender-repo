const pswdBtn = document.getElementById("show-hide-pswd")
pswdBtn.addEventListener("click", function () {
    if (pswdBtn.innerText === "Show") {
        pswdBtn.innerText = "Hide";
        document.getElementById("inputPassword").setAttribute("type", "text");
    } else {
        pswdBtn.innerText = "Show";
        document.getElementById("inputPassword").setAttribute("type", "password");
    }
})