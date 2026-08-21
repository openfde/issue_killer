# Docker 部署

根目录 [README](../../README.md) 是从零启动 Docker 的唯一入口。本页仅补充容器运行细节。

## 必需环境

执行任何 `docker compose` 命令的环境必须有：

```sh
export GH_TOKEN='GitHub token'
export DEEPSEEK_API_KEY='DeepSeek token'
```

容器内不使用宿主机的 `gh` keyring；必须传入 `GH_TOKEN`。配置文件与 `fde-manifests/` 必须在项目根目录。

## 生命周期

```sh
docker compose up -d --build --force-recreate scanner
docker compose ps
docker compose logs -f scanner
docker compose down
```

最后一条保留命名卷；`docker compose down -v` 会删除队列、日志、issue 工件和源码缓存。

## 运行状态

容器内：

```sh
docker compose exec scanner python automation/openfde_ai_server.py \
  --workspace /workspace --config config/openfde-ai-server.json status
docker compose exec scanner sh -lc 'find /workspace/data/logs -type f -print'
```

直接分析指定 issue：

```sh
docker compose exec scanner python automation/openfde_ai_server.py \
  --workspace /workspace --config config/openfde-ai-server.json analyze --issue 470
```
