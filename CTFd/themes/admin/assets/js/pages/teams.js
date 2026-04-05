import "./main";
import CTFd from "../compat/CTFd";
import $ from "jquery";
import "../compat/json";
import { ezAlert, ezQuery } from "../compat/ezq";

function deleteSelectedTeams(_event) {
  let teamIDs = $("input[data-team-id]:checked").map(function () {
    return $(this).data("team-id");
  });
  ezQuery({
    title: "删除队伍",
    body: `确定要删除 ${teamIDs.length} 个队伍吗？`,
    success: function () {
      const reqs = [];
      for (var teamID of teamIDs) {
        reqs.push(
          CTFd.fetch(`/api/v1/teams/${teamID}`, {
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

function bulkEditTeams(_event) {
  let teamIDs = $("input[data-team-id]:checked").map(function () {
    return $(this).data("team-id");
  });

  ezAlert({
    title: "批量编辑队伍",
    body: $(`
    <form id="teams-bulk-edit">
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
      let data = $("#teams-bulk-edit").serializeJSON(true);
      const reqs = [];
      for (var teamID of teamIDs) {
        reqs.push(
          CTFd.fetch(`/api/v1/teams/${teamID}`, {
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
  $("#teams-delete-button").click(deleteSelectedTeams);
  $("#teams-edit-button").click(bulkEditTeams);
});
