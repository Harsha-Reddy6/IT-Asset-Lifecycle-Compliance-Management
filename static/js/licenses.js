/**
 * IT Asset Platform - Software Licenses Script
 */
document.addEventListener("DOMContentLoaded", function () {
  const statusFilter = document.getElementById("licenseStatusFilter");
  if (statusFilter) {
    statusFilter.addEventListener("change", function () {
      this.closest("form").submit();
    });
  }

  // Quick return license seat modal handler
  const returnLicModal = document.getElementById("returnLicenseModal");
  const returnLicForm = document.getElementById("returnLicenseForm");
  const returnLicLabel = document.getElementById("returnLicenseLabel");

  document.querySelectorAll("[data-action='return-license']").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const assignmentId = this.getAttribute("data-assignment-id");
      const licInfo = this.getAttribute("data-license-info");

      if (returnLicModal && returnLicForm) {
        returnLicForm.setAttribute("action", `/license-assignments/return/${assignmentId}`);
        if (returnLicLabel) {
          returnLicLabel.textContent = licInfo;
        }
        returnLicModal.classList.add("active");
      }
    });
  });
});
