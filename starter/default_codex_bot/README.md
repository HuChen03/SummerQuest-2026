# 默认 Codex 飞书机器人

这是学生个人 Agent 的默认实现，完整链路为：飞书 SDK 长连接接收消息、读取学生公开 `PROFILE.md`、调用 Codex 生成带来源回答、使用机器人身份回复。运行时不依赖 `lark-cli`，也不需要任何用户 OAuth 授权。

## 模型配置

模型、供应商和协议由 `bot.py` 设置；AIGW 地址不写入公开仓库，运行时从 `AIGW_BASE_URL` 环境变量读取：

```toml
model = "gpt-5.5"
model_provider = "aigw"
model_reasoning_effort = "high"

[model_providers.aigw]
name = "AI Gateway"
base_url = "<运行时从 AIGW_BASE_URL 读取>"
wire_api = "responses"
env_key = "<读取 bot.toml 中的 codex.api_key_env_key>"
```

每次请求均使用 `codex exec --ephemeral --ignore-user-config`，并为该请求创建临时 `CODEX_HOME`。代码不会读取、修改或依赖学生的 `~/.codex/config.toml`。

## 学生需要配置的内容

安装依赖并复制配置模板：

```bash
python3 -m venv .venv
.venv/bin/pip install -r starter/default_codex_bot/requirements.txt
cp starter/default_codex_bot/config.example.toml \
  starter/default_codex_bot/bot.toml
```

编辑 `bot.toml`：

- `student.name`：学生姓名。
- `student.profile_path`：该同学公开 `PROFILE.md` 的路径，相对 `bot.toml` 解析。
- `feishu.app_id`：个人飞书应用的 App ID。
- `feishu.app_secret_env_key`：保存 App Secret 的环境变量名。
- `codex.base_url_env_key`：保存 AIGW 地址的环境变量名。
- `codex.api_key_env_key`：保存 AIGW API Key 的环境变量名。

AIGW 地址从组织内飞书课程文档获取。地址和实际密钥只写入本地环境变量，不写入 TOML 或 GitHub：

```bash
export FEISHU_APP_SECRET='<个人飞书应用的 App Secret>'
export AIGW_BASE_URL='<从组织内飞书课程文档获取的 AIGW 地址>'
export AIGW_API_KEY='<个人 AIGW API Key>'
```

检查一次本地回答：

```bash
.venv/bin/python starter/default_codex_bot/bot.py \
  --config starter/default_codex_bot/bot.toml \
  --once '请介绍你的研究兴趣'
```

启动自动回复机器人：

```bash
.venv/bin/python starter/default_codex_bot/bot.py \
  --config starter/default_codex_bot/bot.toml
```

机器人只处理私聊文本和富文本消息，群消息默认禁用。对话上下文保存在当前进程内，发送 `/clear` 可以清空当前私聊上下文。普通问题进入 Codex 处理时，机器人会先给原消息添加 `Get` 表情作为“处理中”状态，并在回复完成或处理失败后移除该表情；健康检查和清空上下文不会添加表情。

服务层直接处理 `/ping` 和 `/ping <nonce>`，分别回复 `pong` 和 `pong <nonce>`，不会为健康检查调用模型。该功能用于自愿实践时的本地健康检查，不属于 A0 验收要求。

## 常驻运行

仓库提供同一版本的环境变量和 `systemd --user` 模板：

```bash
mkdir -p ~/.config/openmoss-student-bot ~/.config/systemd/user
cp starter/default_codex_bot/.env.example \
  ~/.config/openmoss-student-bot/env
cp starter/default_codex_bot/openmoss-student-bot.service.example \
  ~/.config/systemd/user/openmoss-student-bot.service
chmod 600 ~/.config/openmoss-student-bot/env
```

从组织内飞书课程文档获取 AIGW 地址，填写本地环境变量，并按实际 clone 位置检查 service 中的路径，然后启动：

```bash
systemctl --user daemon-reload
systemctl --user enable --now openmoss-student-bot.service
systemctl --user status openmoss-student-bot.service
```

不需要开机自启时可以省略 `enable`。常驻运行和重启验证仅用于自愿实践，不属于 A0 要求。

## 飞书开发者后台

应用需要启用机器人能力，并完成以下配置：

1. 开通接收机器人单聊消息、以应用身份发送消息，以及给消息添加和删除 reaction 所需权限。
2. 在事件订阅中选择“使用长连接接收事件”。
3. 订阅 `im.message.receive_v1`。
4. 设置应用可用范围并发布可用版本。

App Secret、AIGW 地址、AIGW API Key、Token、Cookie 和其他内部配置不得写入 GitHub、`bot.toml`、公开日志或个人及作业飞书文档正文。AIGW 地址只从组织内飞书课程文档获取，并保存在本地环境变量或指定密钥系统中。
