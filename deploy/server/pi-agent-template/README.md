# pi-agent 目录模板

`PI_CODING_AGENT_DIR` 指向的持久目录，用于保存 pi 的登录会话与本地配置。

- 服务器上对应 `/aosp/aosp17-ai/pi-agent`（挂载到容器 `/workspace/pi-agent`）。
- 默认模型为 `deepseek/deepseek-flash`（支持图片输入，用于截图证据；`deepseek-v4-pro` 不支持图片）。
- 一键 Docker 部署时，entrypoint 会根据 `PI_PROVIDER`/`PI_MODEL` 生成 `settings.json`；其他提供方需设置对应的 `OPENAI_API_KEY`/`ANTHROPIC_API_KEY`/`GEMINI_API_KEY`/`GOOGLE_API_KEY`，`PI_BASE_URL` 可指向 OpenAI 兼容网关。
- 把 pi 的凭据/配置文件放在这里；不要提交到版本库。
- 检查提供方是否就绪：容器内执行 `pi auth`。
