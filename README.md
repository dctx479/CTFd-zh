# ![CTFd Logo](https://github.com/CTFd/CTFd/blob/master/CTFd/themes/core/static/img/logo.png?raw=true)

![CTFd MySQL CI](https://github.com/CTFd/CTFd/workflows/CTFd%20MySQL%20CI/badge.svg?branch=master)
![Linting](https://github.com/CTFd/CTFd/workflows/Linting/badge.svg?branch=master)
[![MajorLeagueCyber Discourse](https://img.shields.io/discourse/status?server=https%3A%2F%2Fcommunity.majorleaguecyber.org%2F)](https://community.majorleaguecyber.org/)
[![Documentation Status](https://api.netlify.com/api/v1/badges/6d10883a-77bb-45c1-a003-22ce1284190e/deploy-status)](https://docs.ctfd.io)
![Sync Upstream](https://github.com/dctx479/CTFd-zh/actions/workflows/sync-upstream.yml/badge.svg)

---

> **本仓库** 是 [CTFd/CTFd](https://github.com/CTFd/CTFd) 的**简体中文汉化版**，在上游基础上做了以下工作：
> - 全面汉化（模板、后端 Python、JavaScript/Vue 组件、表单字段）
> - 默认语言设置为简体中文，保留多语言切换支持
> - GitHub Actions 自动追踪上游更新并同步汉化
>
> 如需英文原版请访问 [CTFd/CTFd](https://github.com/CTFd/CTFd)。

---

## 什么是 CTFd？

CTFd 是一个专注于易用性和可定制性的 Capture The Flag（夺旗赛）平台。它提供了运行 CTF 比赛所需的一切，并且可以通过插件和主题轻松定制。

![CTFd 积分榜](https://github.com/CTFd/CTFd/blob/master/CTFd/themes/core/static/img/scoreboard.png?raw=true)

## 汉化特性

本仓库在上游基础上实现了全面汉化，覆盖以下层次：

| 层次 | 覆盖范围 | 状态 |
|------|---------|------|
| HTML 模板 | core 用户主题 33 个模板 + admin 后台 68 个模板 | ✅ 完成 |
| Python 后端 | forms/ 表单字段、auth.py 认证消息 | ✅ 完成 |
| JavaScript / Vue | admin assets 下 34 个 JS/Vue 组件 | ✅ 完成 |
| 翻译文件 | 简体中文 462 条（100% 覆盖） | ✅ 完成 |
| 繁体中文 | 186 条（100% 覆盖） | ✅ 完成 |
| 默认语言 | 中文（用户可随时切换） | ✅ 完成 |

### 语言切换

用户可通过以下方式切换语言（优先级从高到低）：
1. 账户设置中的语言选项（永久生效）
2. 导航栏"切换语言"按钮（写入 Cookie）
3. 管理员后台配置的全局默认语言
4. 默认：简体中文

## 功能特性

- 通过管理界面创建题目、分类、提示和 Flag
  - 动态计分题目
  - 可解锁的题目支持
  - 题目插件架构，支持自定义题目类型
  - 静态和正则表达式 Flag
    - 自定义 Flag 插件
  - 可解锁提示
  - 文件上传至服务器或 Amazon S3 兼容后端
  - 限制解题次数与隐藏题目
  - 自动暴力破解防护
- 个人赛与团队赛
  - 支持个人参赛或组队参赛
- 积分榜（自动处理并列名次）
  - 对公众隐藏分数
  - 在指定时间封榜
- 积分曲线图（Top 10 团队对比与个人进度图）
- Markdown 内容管理系统
- SMTP + Mailgun 邮件支持
  - 邮箱验证
  - 忘记密码支持
- 自动开赛和结赛
- 队伍管理、隐藏和封禁
- 通过[插件](https://docs.ctfd.io/docs/plugins/overview)和[主题](https://docs.ctfd.io/docs/themes/overview)接口自定义一切
- CTF 数据的导入与导出存档
- 以及更多功能……

## 安装

1. 安装依赖：`pip install -r requirements.txt`
   - 也可以使用 `prepare.sh` 脚本通过 apt 安装系统依赖。
2. 根据需要修改 [CTFd/config.ini](https://github.com/CTFd/CTFd/blob/master/CTFd/config.ini)。
3. 在终端中使用 `python serve.py` 或 `flask run` 以调试模式启动。

使用自动生成的 Docker 镜像：

```bash
docker run -p 8000:8000 -it ctfd/ctfd
```

或使用源码仓库中的 Docker Compose：

```bash
docker compose up
```

详见 [CTFd 文档](https://docs.ctfd.io/) 的[部署选项](https://docs.ctfd.io/docs/deployment/installation)和[入门指南](https://docs.ctfd.io/tutorials/getting-started/)。

## 在线演示

https://demo.ctfd.io/

## 自动同步上游

本仓库通过 GitHub Actions 每日自动同步上游 [CTFd/CTFd](https://github.com/CTFd/CTFd)：

1. 拉取上游 master 分支最新代码
2. 与本仓库汉化 patch 合并（如有冲突则创建 PR 等待人工处理）
3. 重新提取翻译字符串（`pybabel extract`）
4. 编译翻译文件（`pybabel compile`）
5. 自动推送到本仓库 master 分支

> 工作流文件：[.github/workflows/sync-upstream.yml](.github/workflows/sync-upstream.yml)

## 支持

基础支持可加入 [MajorLeagueCyber 社区](https://community.majorleaguecyber.org/)：[![MajorLeagueCyber Discourse](https://img.shields.io/discourse/status?server=https%3A%2F%2Fcommunity.majorleaguecyber.org%2F)](https://community.majorleaguecyber.org/)

如需商业支持或有特殊项目需求，欢迎[联系我们](https://ctfd.io/contact/)。

## 托管服务

想使用 CTFd 但不想管理基础设施？查看 [CTFd 官网](https://ctfd.io/)了解托管部署服务。

## MajorLeagueCyber

CTFd 与 [MajorLeagueCyber](https://majorleaguecyber.org/) 深度集成。MLC 是一个提供赛事调度、队伍追踪和单点登录的 CTF 数据追踪平台。

通过向 MLC 注册 CTF 赛事，用户可以自动登录、追踪个人和团队成绩、提交 Writeup 并接收重要事件通知。

集成方式：注册账户，创建赛事，在 `CTFd/config.py` 或管理面板的相关配置中填入 Client ID 和 Client Secret：

```python
OAUTH_CLIENT_ID = None
OAUTH_CLIENT_SECRET = None
```

## 致谢

- Logo 设计：[Laura Barbera](http://www.laurabb.com/)
- 主题设计：[Christopher Thompson](https://github.com/breadchris)
- 通知音效：[Terrence Martin](https://soundcloud.com/tj-martin-composer)
- 汉化维护：[dctx479/CTFd-zh](https://github.com/dctx479/CTFd-zh)
