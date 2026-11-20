/**
 * IT Asset Platform - Compliance Script
 */
document.addEventListener("DOMContentLoaded", function () {
  const statusFilter = document.getElementById("complianceStatusFilter");
  if (statusFilter) {
    statusFilter.addEventListener("change", function () {
      this.closest("form").submit();
    });
  }

  const typeFilter = document.getElementById("complianceTypeFilter");
  if (typeFilter) {
    typeFilter.addEventListener("change", function () {
      this.closest("form").submit();
    });
  }
});
