function togglePassword(inputId, button) {
    const passwordInput = document.getElementById(inputId);

    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        button.textContent = "🙈";
        button.setAttribute("aria-label", "Hide password");
    } else {
        passwordInput.type = "password";
        button.textContent = "👁️";
        button.setAttribute("aria-label", "Show password");
    }
}