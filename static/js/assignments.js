/**
 * IT Asset Platform - Asset Assignments Script
 */
document.addEventListener("DOMContentLoaded", function () {
  const statusFilter = document.getElementById("assignmentStatusFilter");
  if (statusFilter) {
    statusFilter.addEventListener("change", function () {
      this.closest("form").submit();
    });
  }

  // Quick return modal handler
  const returnModal = document.getElementById("returnAssetModal");
  const returnForm = document.getElementById("returnAssetForm");
  const returnAssetLabel = document.getElementById("returnAssetLabel");

  document.querySelectorAll("[data-action='return-asset']").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const assignmentId = this.getAttribute("data-assignment-id");
      const assetInfo = this.getAttribute("data-asset-info");

      if (returnModal && returnForm) {
        returnForm.setAttribute("action", `/assignments/return/${assignmentId}`);
        if (returnAssetLabel) {
          returnAssetLabel.textContent = assetInfo;
        }
        returnModal.classList.add("active");
      }
    });
  });
});
