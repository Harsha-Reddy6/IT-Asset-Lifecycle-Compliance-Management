/**
 * IT Asset Lifecycle & License Compliance Platform - Core Vanilla JS
 */

document.addEventListener("DOMContentLoaded", function () {
  // 1. Mobile Sidebar Toggle
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebar = document.querySelector(".app-sidebar");
  const overlay = document.getElementById("sidebarOverlay");

  if (sidebarToggle && sidebar && overlay) {
    sidebarToggle.addEventListener("click", function () {
      sidebar.classList.toggle("show-sidebar");
      overlay.classList.toggle("active");
    });

    overlay.addEventListener("click", function () {
      sidebar.classList.remove("show-sidebar");
      overlay.classList.remove("active");
    });
  }

  // 2. Auto Dismiss Flash Alerts after 6 seconds
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach(function (alert) {
    const closeBtn = alert.querySelector(".alert-close");
    if (closeBtn) {
      closeBtn.addEventListener("click", function () {
        alert.style.opacity = "0";
        setTimeout(() => alert.remove(), 250);
      });
    }
    setTimeout(function () {
      if (document.body.contains(alert)) {
        alert.style.transition = "opacity 0.4s ease";
        alert.style.opacity = "0";
        setTimeout(() => alert.remove(), 400);
      }
    }, 6000);
  });

  // 3. Delete Confirmation Dialog
  const deleteModal = document.getElementById("deleteConfirmModal");
  const deleteForm = document.getElementById("deleteConfirmForm");
  const deleteItemName = document.getElementById("deleteItemName");

  document.querySelectorAll("[data-action='confirm-delete']").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      const formAction = this.getAttribute("data-form-action");
      const itemName = this.getAttribute("data-item-name") || "this record";

      if (deleteForm && deleteModal) {
        deleteForm.setAttribute("action", formAction);
        if (deleteItemName) {
          deleteItemName.textContent = itemName;
        }
        deleteModal.classList.add("active");
      } else {
        // Fallback browser confirm
        if (confirm(`Are you sure you want to delete ${itemName}? This operation cannot be undone.`)) {
          const form = document.createElement("form");
          form.method = "POST";
          form.action = formAction;
          
          const csrfInput = document.querySelector("input[name='csrf_token']");
          if (csrfInput) {
            const hiddenCsrf = document.createElement("input");
            hiddenCsrf.type = "hidden";
            hiddenCsrf.name = "csrf_token";
            hiddenCsrf.value = csrfInput.value;
            form.appendChild(hiddenCsrf);
          }
          document.body.appendChild(form);
          form.submit();
        }
      }
    });
  });

  // Close modals on close button or backdrop click
  document.querySelectorAll(".modal-close-btn, [data-modal-close]").forEach(function (el) {
    el.addEventListener("click", function () {
      const modal = this.closest(".modal-backdrop");
      if (modal) modal.classList.remove("active");
    });
  });

  document.querySelectorAll(".modal-backdrop").forEach(function (modal) {
    modal.addEventListener("click", function (e) {
      if (e.target === this) {
        this.classList.remove("active");
      }
    });
  });
});
