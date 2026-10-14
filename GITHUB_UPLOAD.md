# 将橙信源码上传到 GitHub

这个 ZIP 是交接用的源码包。**先解压，再上传解压后的文件和文件夹**；只上传 ZIP 本身，其他人无法直接在 GitHub 页面逐个查看、修改源码，Render 也不能按本项目的 `render.yaml` 正常部署。

推荐让 `zuoyuhong783-sudo/BNPL` 的仓库拥有者操作：

1. 用拥有该仓库写入权限的 GitHub 账号登录 GitHub Desktop。
2. 在 GitHub Desktop 中克隆 `https://github.com/zuoyuhong783-sudo/BNPL.git`。
3. 将本 ZIP 解压后**里面的全部内容**复制到克隆得到的 `BNPL` 文件夹根目录，包括 `.gitignore` 和 `.python-version`；不要复制或替换该文件夹原有的 `.git` 目录。
4. 在 GitHub Desktop 的 Changes 页面核对文件，提交（Commit）并推送（Push）到 `main`。
5. 打开 GitHub 仓库页面，确认能直接看到 `web_app.py`、`static/`、`rules/` 和 `render.yaml`。

如果操作账号不是仓库拥有者，必须先由拥有者给予该账号仓库写入权限。上传源码并不会自动发布网页；要获得公网演示地址，继续按 `DEPLOYMENT.md` 在 Render 部署。

本项目只供课程演示。公开仓库和公开网页均不应包含真实申请人的身份、征信或还款资料。
