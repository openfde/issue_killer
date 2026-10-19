FROM node:24-bookworm-slim

# 以 Node 24 运行 Pi；Debian bookworm 提供 Python 3.11。
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PI_TELEMETRY=0

ARG NPM_REGISTRY=https://registry.npmjs.org
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       python3 python-is-python3 git gh ca-certificates curl ripgrep util-linux \
    && npm config set registry "$NPM_REGISTRY" \
    && npm install --global --no-audit --no-fund @earendil-works/pi-coding-agent@0.84.2 \
    && useradd --create-home --shell /bin/sh agent \
    && rm -rf /var/lib/apt/lists/*

# Android repo 工具（repo 模式需要；默认 GitHub 同步不依赖它，下载失败不阻塞构建）。
ARG REPO_URL=https://storage.googleapis.com/git-repo-downloads/repo
ARG REPO_FALLBACK_URL=https://mirrors.tuna.tsinghua.edu.cn/git/git-repo/repo
RUN if curl -fsSL "$REPO_URL" -o /usr/local/bin/repo || curl -fsSL "$REPO_FALLBACK_URL" -o /usr/local/bin/repo; then \
        chmod 0755 /usr/local/bin/repo && repo --version; \
    else \
        echo "warning: repo launcher unavailable; github source sync still works"; \
    fi

COPY deploy/docker-entrypoint.sh /usr/local/bin/openfde-entrypoint
COPY deploy/run-scan-loop.sh /usr/local/bin/openfde-scan-loop
COPY --chown=agent:agent deploy/server/pi-agent-template/settings.json /opt/pi-agent-template/settings.json

RUN chmod 0755 /usr/local/bin/openfde-entrypoint /usr/local/bin/openfde-scan-loop

WORKDIR /workspace

COPY --chown=agent:agent . .

RUN mkdir -p /workspace/data /workspace/.fde-ai /workspace/pi-agent \
    && chown agent:agent /workspace/data /workspace/.fde-ai /workspace/pi-agent

USER agent

ENTRYPOINT ["/usr/local/bin/openfde-entrypoint"]

CMD ["/usr/local/bin/openfde-scan-loop"]
