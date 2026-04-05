<template>
  <div class="border-bottom">
    <div>
      <button
        type="button"
        class="close float-right"
        aria-label="Close"
        @click="deleteBracket()"
      >
        <span aria-hidden="true">&times;</span>
      </button>
    </div>

    <div class="row">
      <div class="col-md-9">
        <div class="form-group">
          <label>分组名称</label>
          <input type="text" class="form-control" v-model.lazy="bracket.name" />
          <small class="form-text text-muted">
            分组名称（例如："学生"、"实习生"、"工程师"）
          </small>
        </div>
      </div>

      <div class="col-md-12">
        <div class="form-group">
          <label>分组描述</label>
          <input
            type="text"
            class="form-control"
            v-model.lazy="bracket.description"
          />
          <small class="form-text text-muted">分组描述</small>
        </div>
      </div>

      <div class="col-md-12">
        <label>分组类型</label>
        <select class="custom-select" v-model.lazy="bracket.type">
          <option></option>
          <option value="users">用户</option>
          <option value="teams">队伍</option>
        </select>
        <small class="form-text text-muted">
          如果使用队伍模式且希望分组应用于整个队伍而非个人，请选择"队伍"。
        </small>
      </div>
    </div>

    <div class="row pb-3">
      <div class="col-md-12">
        <div class="d-block">
          <button
            class="btn btn-sm btn-success btn-outlined float-right"
            type="button"
            @click="saveBracket()"
          >
            保存
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CTFd from "../../../compat/CTFd";
import { ezToast } from "../../../compat/ezq";

export default {
  props: {
    index: Number,
    initialBracket: Object,
  },
  data: function () {
    return {
      bracket: this.initialBracket,
    };
  },
  methods: {
    persisted: function () {
      // We're using Math.random() for unique IDs so new items have IDs < 1
      // Real items will have an ID > 1
      return this.bracket.id >= 1;
    },
    saveBracket: function () {
      let body = this.bracket;
      let url = "";
      let method = "";
      let message = "";
      if (this.persisted()) {
        url = `/api/v1/brackets/${this.bracket.id}`;
        method = "PATCH";
        message = "分组已更新！";
      } else {
        url = `/api/v1/brackets`;
        method = "POST";
        message = "分组已创建！";
      }
      CTFd.fetch(url, {
        method: method,
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      })
        .then((response) => {
          return response.json();
        })
        .then((response) => {
          if (response.success === true) {
            this.bracket = response.data;
            ezToast({
              title: "成功",
              body: message,
              delay: 1000,
            });
          }
        });
    },
    deleteBracket: function () {
      if (confirm("确定要删除这个分组吗？")) {
        if (this.persisted()) {
          CTFd.fetch(`/api/v1/brackets/${this.bracket.id}`, {
            method: "DELETE",
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
              if (response.success === true) {
                this.$emit("remove-bracket", this.index);
              }
            });
        } else {
          this.$emit("remove-bracket", this.index);
        }
      }
    },
  },
};
</script>
