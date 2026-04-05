<template>
  <div>
    <div class="form-group">
      <label>搜索用户</label>
      <input
        type="text"
        class="form-control"
        placeholder="搜索用户"
        v-model="searchedName"
        @keyup.down="moveCursor('down')"
        @keyup.up="moveCursor('up')"
        @keyup.enter="selectUser()"
      />
    </div>
    <div class="form-group">
      <span
        class="badge badge-primary mr-1"
        v-for="user in selectedUsers"
        :key="user.id"
      >
        {{ user.name }}
        <a class="btn-fa" @click="removeSelectedUser(user.id)"> &#215;</a>
      </span>
    </div>
    <div class="form-group">
      <div
        class="text-center"
        v-if="
          userResults.length == 0 &&
          this.searchedName != '' &&
          awaitingSearch == false
        "
      >
        <span class="text-muted"> 未找到用户 </span>
      </div>
      <ul class="list-group">
        <li
          :class="{
            'list-group-item': true,
            active: idx === selectedResultIdx,
          }"
          v-for="(user, idx) in userResults"
          :key="user.id"
          @click="selectUser(idx)"
        >
          {{ user.name }}
          <small
            v-if="user.team_id"
            :class="{
              'float-right': true,
              'text-white': idx === selectedResultIdx,
              'text-muted': idx !== selectedResultIdx,
            }"
          >
            已在其他队伍中
          </small>
        </li>
      </ul>
    </div>
    <div class="form-group">
      <button
        class="btn btn-success d-inline-block float-right"
        @click="addUsers()"
      >
        添加用户
      </button>
    </div>
  </div>
</template>

<script>
import CTFd from "../../compat/CTFd";
import { ezQuery } from "../../compat/ezq";
import { htmlEntities } from "@ctfdio/ctfd-js/utils/html";

export default {
  name: "UserAddForm",
  props: {
    team_id: Number,
  },
  data: function () {
    return {
      searchedName: "",
      awaitingSearch: false,
      emptyResults: false,
      userResults: [],
      selectedResultIdx: 0,
      selectedUsers: [],
    };
  },
  methods: {
    searchUsers: function () {
      this.selectedResultIdx = 0;
      if (this.searchedName == "") {
        this.userResults = [];
        return;
      }

      CTFd.fetch(`/api/v1/users?view=admin&field=name&q=${this.searchedName}`, {
        method: "GET",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      })
        .then((response) => {
          return response.json();
        })
        .then((response) => {
          if (response.success) {
            this.userResults = response.data.slice(0, 10);
          }
        });
    },
    moveCursor: function (dir) {
      switch (dir) {
        case "up":
          if (this.selectedResultIdx) {
            this.selectedResultIdx -= 1;
          }
          break;
        case "down":
          if (this.selectedResultIdx < this.userResults.length - 1) {
            this.selectedResultIdx += 1;
          }
          break;
      }
    },
    selectUser: function (idx) {
      if (idx === undefined) {
        idx = this.selectedResultIdx;
      }
      let user = this.userResults[idx];

      // Avoid duplicates
      const found = this.selectedUsers.some(
        (searchUser) => searchUser.id === user.id,
      );
      if (found === false) {
        this.selectedUsers.push(user);
      }

      this.userResults = [];
      this.searchedName = "";
    },
    removeSelectedUser: function (user_id) {
      this.selectedUsers = this.selectedUsers.filter(
        (user) => user.id !== user_id,
      );
    },
    handleAddUsersRequest: function () {
      let reqs = [];

      this.selectedUsers.forEach((user) => {
        let body = { user_id: user.id };
        reqs.push(
          CTFd.fetch(`/api/v1/teams/${this.$props.team_id}/members`, {
            method: "POST",
            credentials: "same-origin",
            headers: {
              Accept: "application/json",
              "Content-Type": "application/json",
            },
            body: JSON.stringify(body),
          }),
        );
      });

      return Promise.all(reqs);
    },
    handleRemoveUsersFromTeams: function () {
      let reqs = [];
      this.selectedUsers.forEach((user) => {
        let body = { user_id: user.id };
        reqs.push(
          CTFd.fetch(`/api/v1/teams/${user.team_id}/members`, {
            method: "DELETE",
            body: JSON.stringify(body),
          }),
        );
      });
      return Promise.all(reqs);
    },
    addUsers: function () {
      let usersInTeams = [];
      this.selectedUsers.forEach((user) => {
        if (user.team_id) {
          usersInTeams.push(user.name);
        }
      });
      if (usersInTeams.length) {
        let users = htmlEntities(usersInTeams.join(", "));
        ezQuery({
          title: "确认移出队伍",
          body: `以下用户当前已在其他队伍中：<br><br> ${users} <br><br>确定要将他们从当前队伍移除并加入此队伍吗？<br><br>他们的所有解题记录、提交、奖励和已解锁提示也将被删除！`,
          success: () => {
            this.handleRemoveUsersFromTeams().then((_resps) => {
              this.handleAddUsersRequest().then((_resps) => {
                window.location.reload();
              });
            });
          },
        });
      } else {
        this.handleAddUsersRequest().then((_resps) => {
          window.location.reload();
        });
      }
    },
  },
  watch: {
    searchedName: function (val) {
      if (this.awaitingSearch === false) {
        // 1 second delay after typing
        setTimeout(() => {
          this.searchUsers();
          this.awaitingSearch = false;
        }, 1000);
      }
      this.awaitingSearch = true;
    },
  },
};
</script>

<style scoped></style>
