/**
 * IT Asset Lifecycle, QR Tracking, License Compliance & Enterprise Service Management System
 * Admin Login Interactive Client-Side Script
 */

document.addEventListener("DOMContentLoaded", function () {
  // Elements
  const loginForm = document.getElementById("adminLoginForm");
  const identifierInput = document.getElementById("identifier");
  const passwordInput = document.getElementById("password");
  const togglePasswordBtn = document.getElementById("togglePasswordBtn");
  const toggleIcon = document.getElementById("toggleIcon");
  const submitBtn = document.getElementById("submitBtn");
  const btnText = document.getElementById("btnText");
  const identifierError = document.getElementById("identifierError");
  const passwordError = document.getElementById("passwordError");

  // 1. Show / Hide Password Functionality
  if (togglePasswordBtn && passwordInput && toggleIcon) {
    togglePasswordBtn.addEventListener("click", function (e) {
      e.preventDefault();
      const isPassword = passwordInput.getAttribute("type") === "password";
      
      if (isPassword) {
        passwordInput.setAttribute("type", "text");
        toggleIcon.classList.remove("bi-eye");
        toggleIcon.classList.add("bi-eye-slash");
        togglePasswordBtn.setAttribute("title", "Hide password");
        togglePasswordBtn.setAttribute("aria-label", "Hide password");
      } else {
        passwordInput.setAttribute("type", "password");
        toggleIcon.classList.remove("bi-eye-slash");
        toggleIcon.classList.add("bi-eye");
        togglePasswordBtn.setAttribute("title", "Show password");
        togglePasswordBtn.setAttribute("aria-label", "Show password");
      }
    });
  }

  // 2. Real-Time Input Validation Cleaners
  function clearError(input, errorElement) {
    input.classList.remove("is-invalid");
    if (errorElement) {
      errorElement.textContent = "";
      errorElement.classList.remove("visible");
    }
  }

  function showError(input, errorElement, message) {
    input.classList.add("is-invalid");
    if (errorElement) {
      errorElement.textContent = message;
      errorElement.classList.add("visible");
    }
  }

  if (identifierInput) {
    identifierInput.addEventListener("input", function () {
      clearError(identifierInput, identifierError);
    });
  }

  if (passwordInput) {
    passwordInput.addEventListener("input", function () {
      clearError(passwordInput, passwordError);
    });
  }

  // 3. Form Validation on Submit
  if (loginForm) {
    loginForm.addEventListener("submit", function (e) {
      let isValid = true;
      const identifierVal = identifierInput ? identifierInput.value.trim() : "";
      const passwordVal = passwordInput ? passwordInput.value : "";

      // Validate Identifier
      if (!identifierVal) {
        showError(identifierInput, identifierError, "Please enter your administrator username or email.");
        isValid = false;
      } else if (identifierVal.length < 3) {
        showError(identifierInput, identifierError, "Username or email must be at least 3 characters.");
        isValid = false;
      }

      // Validate Password
      if (!passwordVal) {
        showError(passwordInput, passwordError, "Please enter your administrator password.");
        isValid = false;
      } else if (passwordVal.length < 4) {
        showError(passwordInput, passwordError, "Password must be at least 4 characters long.");
        isValid = false;
      }

      if (!isValid) {
        e.preventDefault();
        return false;
      }

      // Valid: Show loading spinner and prevent duplicate clicks
      if (submitBtn) {
        submitBtn.classList.add("loading");
        if (btnText) {
          btnText.textContent = "Authenticating...";
        }
      }
    });
  }
});
