import $ from "jquery";

export function copyToClipboard(event, selector) {
  // Select element
  $(selector).select();

  // Copy to clipboard
  document.execCommand("copy");

  // Show tooltip to user
  $(event.target).tooltip({
    title: "已复制！",
    trigger: "manual",
  });
  $(event.target).tooltip("show");

  setTimeout(function () {
    $(event.target).tooltip("hide");
  }, 1500);
}
