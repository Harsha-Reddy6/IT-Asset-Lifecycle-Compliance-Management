/**
 * IT Asset Platform - Employees Script
 */
document.addEventListener("DOMContentLoaded", function () {
  const deptFilter = document.getElementById("empDeptFilter");
  if (deptFilter) {
    deptFilter.addEventListener("change", function () {
      this.closest("form").submit();
    });
  }

  const statusFilter = document.getElementById("empStatusFilter");
  if (statusFilter) {
    statusFilter.addEventListener("change", function () {
      this.closest("form").submit();
    });
  }
});
