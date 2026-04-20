document.addEventListener("DOMContentLoaded", function () {
    const passwordInput = document.getElementById("password");
    const reqBox = document.getElementById("passwordRequirements");

    if (!passwordInput || !reqBox) return;

    const reqLength = document.getElementById("reqLength");
    const reqUpper = document.getElementById("reqUpper");
    const reqLower = document.getElementById("reqLower");
    const reqNumber = document.getElementById("reqNumber");
    const reqSpecial = document.getElementById("reqSpecial");

    passwordInput.addEventListener("focus", () => {
        reqBox.style.display = "block";
    });

    passwordInput.addEventListener("input", () => {
        const val = passwordInput.value;

        toggle(reqLength, val.length >= 12);
        toggle(reqUpper, /[A-Z]/.test(val));
        toggle(reqLower, /[a-z]/.test(val));
        toggle(reqNumber, /[0-9]/.test(val));
        toggle(reqSpecial, /[!@#$%^&*]/.test(val));
    });

    function toggle(el, condition) {
        el.style.color = condition ? "#2ecc71" : "#e74c3c";
    }
});