# OpenFDE Pi 服务器部署

本部署使用 `systemd` timer 定期运行协调器。每个已领取 issue 由非交互 Pi 原子步骤连续推进，直到终态或 `max_atomic_steps_per_issue` 上限；协调器不会把任意 Pi 退出码 `0` 解释为“已修复”。

完整日常命令见[使用指南](usage.md)。

## 安装

1. 将仓库放在 `/opt/openfde-ai/app`，创建运行账户和数据目录：

   ```sh
   sudo useradd --system --home /nonexistent --shell /usr/sbin/nologin openfde-ai
   sudo install -d -o openfde-ai -g openfde-ai -m 0700 /opt/openfde-ai/app/data /opt/openfde-ai/app/.fde-ai
   ```

2. 复制 [示例配置](../../config/openfde-ai-server.example.json) 为 `config/openfde-ai-server.json`，保留 `worker.execute=true`；设置合适的 `max_atomic_steps_per_issue`。
3. 基于 [环境变量示例](../../deploy/systemd/openfde-ai.env.example) 创建 `/etc/openfde-ai/openfde-ai.env`，权限 `0600`。其中包含模型与 GitHub 凭据，不能写入项目配置。
4. 安装并启动 timer：

   ```sh
   sudo cp deploy/systemd/openfde-ai-scan.service /etc/systemd/system/
   sudo cp deploy/systemd/openfde-ai-scan.timer /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now openfde-ai-scan.timer
   ```

## 运维

```sh
sudo systemctl status openfde-ai-scan.timer
sudo journalctl -u openfde-ai-scan.service -f
sudo -u openfde-ai python3 /opt/openfde-ai/app/automation/openfde_ai_server.py \
  --workspace /opt/openfde-ai/app \
  --config config/openfde-ai-server.json status
```

停止新的自动分析但保留数据：

```sh
sudo systemctl disable --now openfde-ai-scan.timer
```

将 `worker.execute` 改为 `false` 仅保留 issue 发现与入队。系统不会发布评论、修改源码、应用 patch 或运行构建/测试。
