# pi-agent 目录模板

`PI_CODING_AGENT_DIR` 指向的持久目录，用于保存 pi 的登录会话与本地配置。

- 服务器上对应 `/aosp/aosp17-ai/pi-agent`（挂载到容器 `/workspace/pi-agent`）。
- 把 pi 的凭据/配置文件放在这里；不要提交到版本库。
- 首次使用时在容器内完成登录/模型配置：

```sh
/aosp/aosp17-docker/dk exec -it aosp17-ai pi
```
