import "./main";
import CTFd from "../compat/CTFd";
import $ from "jquery";
import { ezQuery } from "../compat/ezq";

function deleteSelectedUsers(_event) {
  let pageIDs = $("input[data-page-id]:checked").map(function () {
    return $(this).data("page-id");
  });
  ezQuery({
    title: "删除页面",
    body: `确定要删除 ${pageIDs.length} 个页面吗？`,
    success: function () {
      const reqs = [];
      for (var pageID of pageIDs) {
        reqs.push(
          CTFd.fetch(`/api/v1/pages/${pageID}`, {
            method: "DELETE",
          }),
        );
      }
      Promise.all(reqs).then((_responses) => {
        window.location.reload();
      });
    },
  });
}

$(() => {
  $("#pages-delete-button").click(deleteSelectedUsers);
});
