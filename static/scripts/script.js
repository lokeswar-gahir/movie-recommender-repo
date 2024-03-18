document.querySelector('#mode').addEventListener('click', function (event) {
    modeBtn = event['target'];
    if (modeBtn.innerText === 'Dark Mode') {
        document.querySelector('html').setAttribute('data-bs-theme', 'dark')
        modeBtn.innerText = "Light Mode";
        localStorage.setItem("theme", 'dark')
    } else {
        document.querySelector('html').setAttribute('data-bs-theme', 'light')
        modeBtn.innerText = "Dark Mode";
        localStorage.setItem("theme", 'light')
    }
})