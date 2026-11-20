/**
 * IT Asset Platform - Asset Management Script
 */
document.addEventListener("DOMContentLoaded", function () {
  // Quick status filter change handler
  const statusFilter = document.getElementById("assetStatusFilter");
  if (statusFilter) {
    statusFilter.addEventListener("change", function () {
      this.closest("form").submit();
    });
  }

  const categoryFilter = document.getElementById("assetCategoryFilter");
  if (categoryFilter) {
    categoryFilter.addEventListener("change", function () {
      this.closest("form").submit();
    });
  }
});
