import "./main";
import $ from "jquery";
import { ezQuery } from "../compat/ezq";

function reset(event) {
  event.preventDefault();
  ezQuery({
    title: "重置 CTF？",
    body: "确定要重置 CTFd 实例吗？",
    success: function () {
      $("#reset-ctf-form").off("submit").submit();
    },
  });
}

$(() => {
  $("#reset-ctf-form").submit(reset);
});
