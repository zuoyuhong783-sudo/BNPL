# 公开演示部署说明（Render）

本项目是课程演示原型，不是实际授信服务。公开链接没有账号验证；只可使用虚构测试数据，不要输入真实身份、征信、还款或其他个人资料。

## 部署前准备

1. 在本地解压完整项目，确认根目录同时包含 `render.yaml`、`web_app.py`、`requirements.txt`、`rules/` 和 `static/`。
2. 本地先运行 `python -m pip install -r requirements.txt` 和 `python -m unittest discover -s tests -v`。
3. 将项目源码放进你有权限的 Git 仓库；仓库可以是私有的。不要上传 `.venv/`、`__pycache__/`、真实申请资料或凭证。

## 在 Render 创建公开网页

1. 登录 [Render](https://dashboard.render.com/)，连接上述 Git 仓库。
2. 选择 **New → Blueprint**，选中包含 `render.yaml` 的仓库并按页面提示创建服务。
3. Blueprint 会使用 Python 3.12、安装 `requirements.txt`，再以 `0.0.0.0:$PORT` 启动服务。`/healthz` 用作健康检查。
4. 部署成功后，Render 会显示一个 `https://...onrender.com` 地址。把该地址发给不同网络的组员，用手机流量实际测试一次。

如果服务名 `bnpl-expert-demo` 已被占用，先修改 `render.yaml` 中的 `name`，再重新部署。不要以为本地页面 `http://127.0.0.1:8765/` 就是公网地址。

## 展示前检查

- 依次试跑四类虚构用户，确认提交、CF、额度及目标诊断能正常显示。
- 使用另一台设备、另一种网络测试公网链接。
- Render 免费服务闲置一段时间后会休眠；正式展示前提前打开链接并等待其唤醒。若需要持续可用，应选用不休眠的服务计划。
- 程序不会把申请资料保存为记录，但填写的数据会经过网络发送到部署服务器。公开演示不得采集真实个人信用资料。
- 目前没有登录、访问频率限制或正式审计机制；若要用于真实业务，必须先补充安全与合规设计。

本地运行方式不变：`python web_app.py` 默认仍只监听 `127.0.0.1:8765`。云端由 `render.yaml` 传入 `--host 0.0.0.0`，并通过环境变量 `PORT` 指定端口。
