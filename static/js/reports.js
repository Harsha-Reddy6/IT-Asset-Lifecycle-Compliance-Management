/**
 * IT Asset Platform - Reports and Analytics Script
 */
document.addEventListener("DOMContentLoaded", function () {
  const reportStatusFilter = document.getElementById("reportStatusFilter");
  if (reportStatusFilter) {
    reportStatusFilter.addEventListener("change", function () {
      this.closest("form").submit();
    });
  }

  const reportCategoryFilter = document.getElementById("reportCategoryFilter");
  if (reportCategoryFilter) {
    reportCategoryFilter.addEventListener("change", function () {
      this.closest("form").submit();
    });
  }
});
