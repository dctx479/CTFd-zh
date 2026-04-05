import "./main";
import CTFd from "../compat/CTFd";
import $ from "jquery";
import "../compat/json";
import { ezAlert, ezQuery } from "../compat/ezq";

function deleteSelectedUsers(_event) {
  let userIDs = $("input[data-user-id]:checked").map(function () {
    return $(this).data("user-id");
  });
  let target = userIDs.length === 1 ? "user" : "users";

  ezQuery({
    title: "删除用户",
    body: `确定要删除 ${userIDs.length} 个用户吗？`,
    success: function () {
      const reqs = [];
      for (var userID of userIDs) {
        reqs.push(
          CTFd.fetch(`/api/v1/users/${userID}`, {
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

function bulkEditUsers(_event) {
  let userIDs = $("input[data-user-id]:checked").map(function () {
    return $(this).data("user-id");
  });

  ezAlert({
    title: "批量编辑用户",
    body: $(`
    <form id="users-bulk-edit">
      <div class="form-group">
        <label>已验证</label>
        <select name="verified" data-initial="">
          <option value="">--</option>
          <option value="true">是</option>
          <option value="false">否</option>
        </select>
      </div>
      <div class="form-group">
        <label>已封禁</label>
        <select name="banned" data-initial="">
          <option value="">--</option>
          <option value="true">是</option>
          <option value="false">否</option>
        </select>
      </div>
      <div class="form-group">
        <label>已隐藏</label>
        <select name="hidden" data-initial="">
          <option value="">--</option>
          <option value="true">是</option>
          <option value="false">否</option>
        </select>
      </div>
    </form>
    `),
    button: "提交",
    success: function () {
      let data = $("#users-bulk-edit").serializeJSON(true);
      const reqs = [];
      for (var userID of userIDs) {
        reqs.push(
          CTFd.fetch(`/api/v1/users/${userID}`, {
            method: "PATCH",
            body: JSON.stringify(data),
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
  $("#users-delete-button").click(deleteSelectedUsers);
  $("#users-edit-button").click(bulkEditUsers);
});
